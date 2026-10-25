import asyncio, logging, contextlib
from collections.abc import Mapping, Sequence
from typing import Any, Optional

import msgspec
from aiokafka import AIOKafkaProducer as RedpandaAsyncProducer
from aiokafka.errors import KafkaConnectionError as RedpandaConnectionError
from aiokafka.errors import KafkaError as RedpandaClientError
from aiokafka.helpers import create_ssl_context as create_redpanda_ssl_context

from src.vortex.shared.exceptions import RedpandaNotStartedError, RedpandaPublishError
from src.vortex.shared.config import get_settings

# Why we dont need batching now with redpanda

# REDIS -> Every event we send is its own small request
# redis wont group it for us we need to group them in memory

# Redpanda sends event batches as the basic unit, and the client library
# groups published events automatically:


# Redpanda producer
_redpanda_producer: Optional[RedpandaAsyncProducer] = None
_lifecycle_lock = asyncio.Lock()

logger = logging.getLogger(__name__)

# --- settings ---
settings = get_settings()


class RedpandaProducer:
    @staticmethod
    async def start() -> None:
        """start the producer"""

        global _redpanda_producer

        async with _lifecycle_lock:
            if _redpanda_producer is not None:
                return

            protocol = settings.redpanda.security_protocol

            config: dict[str, Any] = {
                "bootstrap_servers": settings.redpanda.bootstrap_servers,
                # just an name tag for our appp
                "client_id": settings.redpanda.client_id,
                # all -> wait until the main machine and all its backup copies have it
                # 1 ->  wait until the main machine has it.
                "acks": "all",
                # true -> requires "acks":all
                # avoid repeats
                "enable_idempotence": True,
                # compress the messages to avoid network bandwidth
                "compression_type": "gzip",
                # how long the producer waits for Redpanda to answer before giving up on that attempt
                "request_timeout_ms": settings.redpanda.request_timeout_ms,
                # max batch size after which send all events
                "max_batch_size": settings.redpanda.max_batch_size,
                "security_protocol": protocol,
            }

            if protocol == "PLAINTEXT":
                pass
            elif protocol == "SASL_SSL":
                config["ssl_context"] = create_redpanda_ssl_context()
                config["sasl_mechanism"] = settings.redpanda.sasl_mechanism
                config["sasl_plain_username"] = settings.redpanda.sasl_username
                config["sasl_plain_password"] = settings.redpanda.sasl_password

            last_error: Optional[Exception] = None
            for attempt in range(1, settings.redpanda.start_max_attempts + 1):
                producer = RedpandaAsyncProducer(**config)
                try:
                    await producer.start()
                except (RedpandaConnectionError, RedpandaClientError, OSError) as exc:
                    last_error = exc

                    with contextlib.suppress(Exception):
                        await producer.stop()

                    if attempt == settings.redpanda.start_max_attempts:
                        break

                    delay = min(2**attempt, 30)

                    logger.warning(
                        "Redpanda start failed (attempt %d/%d): %s. Retrying in %ds",
                        attempt,
                        settings.redpanda.start_max_attempts,
                        exc,
                        delay,
                    )

                    await asyncio.sleep(delay)
                    continue

                _redpanda_producer = producer
                logger.info(
                    "Redpanda producer started (servers=%s)",
                    settings.redpanda.bootstrap_servers,
                )
                return

            raise RedpandaPublishError(
                f"Could not connect to Redpanda after "
                f"{settings.redpanda.start_max_attempts} attempts"
            ) from last_error

    @staticmethod
    async def stop() -> None:
        """Flush pending messages and close the producer"""
        global _redpanda_producer

        async with _lifecycle_lock:
            producer, _redpanda_producer = _redpanda_producer, None
            if producer is None:
                return
            try:
                await asyncio.wait_for(producer.stop(), timeout=10)
            except Exception as exc:  # shutdown must never raise
                logger.warning("Error while stopping Redpanda producer: %s", exc)
            logger.info("Redpanda producer stopped")

    @staticmethod
    async def send_events(
        payloads: Sequence[Mapping[str, Any] | msgspec.Struct],
        topic: str,
        partition: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        if not payloads:
            return []
        if _redpanda_producer is None:
            raise RedpandaNotStartedError("Redpanda producer is not started")

        try:
            values = [
                msgspec.json.encode(payload)
                for payload in payloads
            ]
        except (TypeError, msgspec.EncodeError) as exc:
            raise RedpandaPublishError(f"Payload is not serializable: {exc}") from exc

        return await RedpandaProducer.send_serialized_events(
            values, topic=topic, partition=partition
        )

    @staticmethod
    async def send_serialized_events(
        values: Sequence[bytes],
        topic: str,
        partition: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Publish already encoded JSON values without serializing them again."""
        producer = _redpanda_producer
        if producer is None:
            raise RedpandaNotStartedError("Redpanda producer is not started")
        if not values:
            return []

        try:
            # Queue every record first so the producer can fill its partition batches,
            # then await the delivery acknowledgements within one overall deadline.
            async with asyncio.timeout(settings.redpanda.send_timeout_seconds):
                queued = await asyncio.gather(
                    *(
                        producer.send(topic=topic, value=value, partition=partition)
                        for value in values
                    ),
                    return_exceptions=True,
                )
                queue_errors = [
                    item for item in queued if isinstance(item, BaseException)
                ]
                delivery_futures = [
                    item for item in queued if not isinstance(item, BaseException)
                ]
                delivered = await asyncio.gather(
                    *delivery_futures,
                    return_exceptions=True,
                )
                delivery_errors = [
                    item for item in delivered if isinstance(item, BaseException)
                ]
                errors = queue_errors + delivery_errors
                if errors:
                    if isinstance(errors[0], asyncio.CancelledError):
                        raise errors[0]
                    raise RedpandaPublishError(
                        f"Could not publish every event in batch ({len(errors)} failures)"
                    ) from errors[0]
                metadata_items = delivered
        except asyncio.TimeoutError as exc:
            logger.error("Redpanda batch send timed out (count=%d)", len(values))
            raise RedpandaPublishError("Timed out publishing batch to Redpanda") from exc
        except RedpandaClientError as exc:
            logger.error("Redpanda batch send failed: %s", exc)
            raise RedpandaPublishError(f"Redpanda publish failed: {exc}") from exc

        logger.info(
            "Batch published (topic=%s count=%d first_partition=%d first_offset=%d)",
            topic,
            len(metadata_items),
            metadata_items[0].partition,
            metadata_items[0].offset,
        )
        return [
            {
                "topic": metadata.topic,
                "partition": metadata.partition,
                "offset": metadata.offset,
            }
            for metadata in metadata_items
        ]
