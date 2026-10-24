import asyncio, logging, orjson, contextlib
from collections.abc import Mapping
from typing import Any, Optional

from aiokafka import AIOKafkaProducer as RedpandaAsyncProducer
from aiokafka.errors import KafkaConnectionError as RedpandaConnectionError
from aiokafka.errors import KafkaError as RedpandaClientError
from aiokafka.helpers import create_ssl_context

from src.vortex.shared.exceptions import RedpandaNotStartedError, RedpandaPublishError
from src.vortex.shared.config import get_settings

# Why we dont need batching now with redpanda

# REDIS -> Every event we send is its own small request
# redis wont group it for us we need to group them in memory

# Kafka and Redpanda were designed around batches from day one. 
# Their wire protocol doesn’t send “one event.”
# It sends “a batch of events” as the basic unit. 
# So the client library does the grouping automatically:


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
                config["ssl_context"] = create_ssl_context()
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
    async def send_event(
        payload: Mapping[str, Any],
        topic: str,
        partition: Optional[int] = None,
    ) -> dict[str, Any]:
        """Publish an event without a key so the partitioner can distribute it."""
        return await RedpandaProducer._send(
            payload=payload,
            topic=topic,
            partition=partition,
        )

    @staticmethod
    async def _send(
        payload: Mapping[str, Any],
        topic: str,
        partition: Optional[int],
    ) -> dict[str, Any]:
        producer = _redpanda_producer
        if producer is None:
            raise RedpandaNotStartedError("Redpanda producer is not started")

        try:
            value = orjson.dumps(payload, option=orjson.OPT_NON_STR_KEYS)
        except orjson.JSONEncodeError as exc:
            raise RedpandaPublishError(f"Payload is not serializable: {exc}") from exc

        try:
            metadata = await asyncio.wait_for(
                producer.send_and_wait(
                    topic=topic,
                    value=value,
                    partition=partition,
                ),
                timeout=settings.redpanda.send_timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            logger.error("Redpanda send timed out")
            raise RedpandaPublishError("Timed out publishing to Redpanda") from exc
        except RedpandaClientError as exc:
            logger.error("Redpanda send failed: %s", exc)
            raise RedpandaPublishError(f"Redpanda publish failed: {exc}") from exc

        logger.info(
            "Message published (topic=%s partition=%d offset=%d)",
            metadata.topic,
            metadata.partition,
            metadata.offset,
        )
        return {
            "topic": metadata.topic,
            "partition": metadata.partition,
            "offset": metadata.offset,
        }
