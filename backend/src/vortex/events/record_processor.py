import asyncio
import base64
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import msgspec
from sqlalchemy.exc import DataError as DatabaseDataError
from sqlalchemy.exc import IntegrityError as DatabaseIntegrityError

from src.vortex.shared.config import get_settings
from src.vortex.shared.database import SessionFactory
from src.vortex.shared.exceptions import InvalidEventError
from src.vortex.shared.redpanda_client import RedpandaProducer

from .schemas import EventIngestionSchema
from .services import EventService, invalid_identify_indexes

logger = logging.getLogger(__name__)


def _decode_event(message: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        payload = msgspec.json.decode(message.value)
        if not isinstance(payload, dict):
            raise ValueError("event message must be a JSON object")
        # Redpanda records are already JSON-decoded above. Validate the event
        # fields with msgspec while retaining the full payload and its metadata.
        msgspec.convert(payload, EventIngestionSchema, strict=False)
        UUID(str(payload["tenant_id"]))
        UUID(str(payload["organization_id"]))
        UUID(str(payload["api_key_id"]))
        received_at = payload.get("received_at")
        if received_at is not None:
            if not isinstance(received_at, str):
                raise ValueError("received_at must be an ISO 8601 string")
            datetime.fromisoformat(received_at.replace("Z", "+00:00"))
    except (
        msgspec.DecodeError,
        msgspec.ValidationError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        raise InvalidEventError(str(exc)) from exc

    return payload, {
        "topic": message.topic,
        "partition": message.partition,
        "offset": message.offset,
    }


def _is_permanent_record_error(exc: Exception) -> bool:
    if isinstance(exc, (DatabaseDataError, ValueError)):
        return True

    original = getattr(exc, "orig", None)
    sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
    if isinstance(sqlstate, str):
        return sqlstate[:2] in {"22", "23"}
    return isinstance(exc, DatabaseIntegrityError)


def _dead_letter_payload(message: Any, exc: Exception) -> dict[str, Any]:
    raw_bytes = message.value or b""
    try:
        raw_value = raw_bytes.decode("utf-8")
        raw_value_encoding = "utf-8"
    except UnicodeDecodeError:
        raw_value = base64.b64encode(raw_bytes).decode("ascii")
        raw_value_encoding = "base64"

    return {
        "dlq_id": f"{message.topic}:{message.partition}:{message.offset}",
        "source": {
            "topic": message.topic,
            "partition": message.partition,
            "offset": message.offset,
        },
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "error": {
            "type": type(exc).__name__,
            "message": str(exc)[:2000],
        },
        "raw_value": raw_value,
        "raw_value_encoding": raw_value_encoding,
        "raw_value_is_null": message.value is None,
    }


async def _send_to_dlq(message: Any, exc: Exception) -> None:
    settings = get_settings().redpanda
    await RedpandaProducer.send_events(
        [_dead_letter_payload(message, exc)],
        topic=settings.dlq_topic,
        partition=message.partition,
    )
    logger.warning(
        "Sent invalid event to DLQ (source_topic=%s partition=%s offset=%s reason=%s)",
        message.topic,
        message.partition,
        message.offset,
        type(exc).__name__,
    )


async def _persist_valid_batch(
    records: list[tuple[Any, dict[str, Any], dict[str, Any]]],
) -> None:
    if not records:
        return

    values = [(payload, metadata) for _, payload, metadata in records]
    try:
        async with SessionFactory.begin() as session:
            await EventService.process_batch(values, session)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        if not _is_permanent_record_error(exc):
            raise

        if len(records) == 1:
            await _send_to_dlq(records[0][0], exc)
            return

        midpoint = len(records) // 2
        logger.warning(
            "Splitting batch after permanent record error (count=%d)", len(records)
        )
        await _persist_valid_batch(records[:midpoint])
        await _persist_valid_batch(records[midpoint:])


async def persist_records(records: list[Any]) -> None:
    """Persist valid events and dead-letter permanent record failures."""
    values: list[tuple[Any, dict[str, Any], dict[str, Any]]] = []
    invalid: list[tuple[Any, Exception]] = []
    for message in records:
        try:
            payload, metadata = _decode_event(message)
            values.append((message, payload, metadata))
        except InvalidEventError as exc:
            invalid.append((message, exc))

    if values:
        identify_records = [(payload, metadata) for _, payload, metadata in values]
        invalid_indexes = invalid_identify_indexes(identify_records)
        for index in sorted(invalid_indexes):
            message, _, _ = values[index]
            invalid.append(
                (message, InvalidEventError("ambiguous or invalid $identify event"))
            )
        values = [
            item for index, item in enumerate(values) if index not in invalid_indexes
        ]

    # A DLQ publish must be acknowledged before the caller can commit source offsets.
    for message, exc in sorted(
        invalid, key=lambda item: (item[0].topic, item[0].partition, item[0].offset)
    ):
        await _send_to_dlq(message, exc)

    await _persist_valid_batch(values)
