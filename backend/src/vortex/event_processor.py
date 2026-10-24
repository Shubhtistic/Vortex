import asyncio
import logging
import signal
from typing import Any

from aiokafka import AIOKafkaConsumer as RedpandaConsumer
from aiokafka.errors import KafkaError as RedpandaClientError
from aiokafka.helpers import create_ssl_context as create_redpanda_ssl_context
from aiokafka.structs import (
    OffsetAndMetadata as RedpandaOffsetAndMetadata,
    TopicPartition as RedpandaTopicPartition,
)

from src.vortex.shared.config import get_settings
from src.vortex.shared.database import db_engine
from src.vortex.shared.redpanda_client import RedpandaProducer

from src.vortex.events.record_processor import persist_records

logger = logging.getLogger(__name__)
BATCH_SIZE = 5000


def _consumer_config() -> dict[str, Any]:
    settings = get_settings().redpanda
    config: dict[str, Any] = {
        "bootstrap_servers": settings.bootstrap_servers,
        "client_id": f"{settings.client_id}-event-processor",
        "group_id": settings.consumer_group_id,
        "enable_auto_commit": False,
        "auto_offset_reset": "earliest",
        "max_poll_records": BATCH_SIZE,
        "max_poll_interval_ms": 3_600_000,
        "security_protocol": settings.security_protocol,
    }
    if settings.security_protocol == "SASL_SSL":
        config.update(
            ssl_context=create_redpanda_ssl_context(),
            sasl_mechanism=settings.sasl_mechanism,
            sasl_plain_username=settings.sasl_username,
            sasl_plain_password=settings.sasl_password,
        )
    return config


async def run() -> None:
    settings = get_settings().redpanda
    consumer: RedpandaConsumer | None = None
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    pending_records: list[Any] = []
    try:
        if settings.events_topic == settings.dlq_topic:
            raise ValueError("REDPANDA_EVENTS_TOPIC and REDPANDA_DLQ_TOPIC must differ")

        await RedpandaProducer.start()
        while not stop.is_set():
            consumer = RedpandaConsumer(settings.events_topic, **_consumer_config())
            try:
                await consumer.start()
                logger.info(
                    "Redpanda event consumer started (topic=%s group=%s)",
                    settings.events_topic,
                    settings.consumer_group_id,
                )
                break
            except (RedpandaClientError, OSError):
                logger.exception("Could not connect to Redpanda; retrying in 5 seconds")
                await consumer.stop()
                consumer = None
                await asyncio.sleep(5)

        if consumer is None:
            return
        while not stop.is_set():
            if pending_records:
                records = pending_records[:BATCH_SIZE]
                pending_records = pending_records[BATCH_SIZE:]
            else:
                polled = await consumer.getmany(timeout_ms=1000, max_records=BATCH_SIZE)
                records = [
                    message for messages in polled.values() for message in messages
                ]
            if not records:
                continue
            records.sort(
                key=lambda message: (message.topic, message.partition, message.offset)
            )

            # Keep this exact polled batch in memory and leave offsets untouched
            # until its complete Postgres transaction succeeds.
            while not stop.is_set():
                try:
                    await persist_records(records)
                    offsets = {}
                    for message in records:
                        partition = RedpandaTopicPartition(
                            message.topic, message.partition
                        )
                        next_offset = message.offset + 1
                        current = offsets.get(partition)
                        if current is None or next_offset > current.offset:
                            offsets[partition] = RedpandaOffsetAndMetadata(
                                next_offset, ""
                            )
                    if offsets:
                        await consumer.commit(offsets)
                    break
                except Exception:
                    logger.exception(
                        "Event batch failed; offsets remain uncommitted and will retry"
                    )
                    # Poll while retrying so the consumer group remains alive.
                    # Pausing assigned partitions prevents new reads from racing
                    # ahead of the batch whose database transaction failed.
                    try:
                        consumer.pause(*consumer.assignment())
                        polled = await consumer.getmany(
                            timeout_ms=1000, max_records=BATCH_SIZE
                        )
                        pending_records.extend(
                            message
                            for messages in polled.values()
                            for message in messages
                        )
                        pending_records.sort(
                            key=lambda message: (
                                message.topic,
                                message.partition,
                                message.offset,
                            )
                        )
                        consumer.pause(*consumer.assignment())
                    except Exception:
                        logger.exception("Consumer poll failed during database retry")
                    await asyncio.sleep(1)
            consumer.resume(*consumer.assignment())
    finally:
        try:
            if consumer is not None:
                await consumer.stop()
        finally:
            try:
                await RedpandaProducer.stop()
            finally:
                await db_engine.dispose()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())


if __name__ == "__main__":
    main()
