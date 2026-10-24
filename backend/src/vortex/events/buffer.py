import asyncio
import logging
import time
from collections.abc import Mapping, Sequence
from typing import Any

import orjson
from fastapi import HTTPException, status

from src.vortex.shared.config import get_settings
from src.vortex.shared.redpanda_client import RedpandaProducer

logger = logging.getLogger(__name__)
settings = get_settings()

EventItem = tuple[Mapping[str, Any], int]
_STOP = object()


class EventBuffer:
    """Bounded in-memory queue that flushes accepted events to Redpanda."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[EventItem | object] = asyncio.Queue(
            maxsize=settings.event_buffer.max_pending_events
        )
        self._worker: asyncio.Task[None] | None = None
        self._accepting = False
        self._pending_events = 0
        self._pending_bytes = 0

    async def start(self) -> None:
        if self._worker is not None and not self._worker.done():
            return
        self._accepting = True
        self._worker = asyncio.create_task(self._flush_loop(), name="event-buffer-flusher")
        logger.info(
            "Event buffer started (flush_size=%d flush_interval=%.3fs max_events=%d max_bytes=%d)",
            settings.event_buffer.max_batch_size,
            settings.event_buffer.flush_interval_seconds,
            settings.event_buffer.max_pending_events,
            settings.event_buffer.max_pending_bytes,
        )

    def enqueue(self, events: Sequence[Mapping[str, Any]]) -> None:
        """Accept a whole request atomically, or reject it without partial enqueue."""
        if not events:
            return
        if not self._accepting or self._worker is None or self._worker.done():
            raise self._unavailable_response()

        try:
            sized_events = [
                (event, len(orjson.dumps(event, option=orjson.OPT_NON_STR_KEYS)))
                for event in events
            ]
        except (TypeError, orjson.JSONEncodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Event batch contains a value that cannot be serialized",
            ) from exc

        batch_bytes = sum(size for _, size in sized_events)
        if batch_bytes > settings.event_buffer.max_pending_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Event batch exceeds the configured buffer byte limit",
            )

        if (
            self._pending_events + len(sized_events)
            > settings.event_buffer.max_pending_events
            or self._pending_bytes + batch_bytes
            > settings.event_buffer.max_pending_bytes
        ):
            logger.warning(
                "Rejected event batch because buffer is full "
                "(request_events=%d request_bytes=%d pending_events=%d pending_bytes=%d)",
                len(sized_events),
                batch_bytes,
                self._pending_events,
                self._pending_bytes,
            )
            raise self._full_response()

        # No await occurs between capacity validation and enqueue, so another
        # request cannot take this capacity midway through the operation.
        for item in sized_events:
            self._queue.put_nowait(item)
        self._pending_events += len(sized_events)
        self._pending_bytes += batch_bytes

    async def stop(self) -> None:
        worker = self._worker
        self._accepting = False
        if worker is None:
            return

        if not worker.done():
            try:
                deadline = time.monotonic() + settings.event_buffer.shutdown_timeout_seconds
                # The sentinel follows all accepted events, so normal shutdown
                # drains the queue before the Redpanda producer is closed.
                await asyncio.wait_for(
                    self._queue.put(_STOP),
                    timeout=max(0, deadline - time.monotonic()),
                )
                await asyncio.wait_for(
                    asyncio.shield(worker),
                    timeout=max(0, deadline - time.monotonic()),
                )
            except asyncio.TimeoutError:
                logger.error(
                    "Timed out draining event buffer during shutdown "
                    "(pending_events=%d pending_bytes=%d)",
                    self._pending_events,
                    self._pending_bytes,
                )
                worker.cancel()
                await asyncio.gather(worker, return_exceptions=True)
            except Exception:
                logger.exception("Event buffer failed during shutdown")
                worker.cancel()
                await asyncio.gather(worker, return_exceptions=True)

        self._worker = None
        logger.info(
            "Event buffer stopped (pending_events=%d pending_bytes=%d)",
            self._pending_events,
            self._pending_bytes,
        )

    async def _flush_loop(self) -> None:
        stop_after_batch = False
        while True:
            first = await self._queue.get()
            if first is _STOP:
                self._queue.task_done()
                return

            batch: list[EventItem] = [first]
            batch_bytes = first[1]
            deadline = time.monotonic() + settings.event_buffer.flush_interval_seconds

            while len(batch) < settings.event_buffer.max_batch_size:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    item = await asyncio.wait_for(self._queue.get(), timeout=remaining)
                except asyncio.TimeoutError:
                    break

                if item is _STOP:
                    self._queue.task_done()
                    stop_after_batch = True
                    break

                event_item = item
                batch.append(event_item)
                batch_bytes += event_item[1]

            await self._publish_with_retry(batch)
            self._pending_events -= len(batch)
            self._pending_bytes -= batch_bytes
            for _ in batch:
                self._queue.task_done()

            logger.debug(
                "Flushed event batch (count=%d bytes=%d pending=%d)",
                len(batch),
                batch_bytes,
                self._pending_events,
            )
            if stop_after_batch:
                return

    async def _publish_with_retry(self, batch: Sequence[EventItem]) -> None:
        delay_seconds = 1.0
        while True:
            try:
                await RedpandaProducer.send_events(
                    [event for event, _ in batch],
                    topic=settings.redpanda.events_topic,
                )
                return
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Could not publish event batch; retaining it and retrying "
                    "(count=%d retry_in_seconds=%.1f)",
                    len(batch),
                    delay_seconds,
                )
                await asyncio.sleep(delay_seconds)
                delay_seconds = min(delay_seconds * 2, 30.0)

    @staticmethod
    def _full_response() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event buffer is full; retry this batch shortly",
            headers={"Retry-After": "1"},
        )

    @staticmethod
    def _unavailable_response() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event buffer is not available; retry shortly",
            headers={"Retry-After": "1"},
        )


event_buffer = EventBuffer()


async def start_event_buffer() -> None:
    await event_buffer.start()


async def stop_event_buffer() -> None:
    await event_buffer.stop()


def enqueue_events(events: Sequence[Mapping[str, Any]]) -> None:
    event_buffer.enqueue(events)
