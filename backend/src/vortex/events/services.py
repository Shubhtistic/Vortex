import logging
import ipaddress
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5, uuid7

from sqlalchemy.ext.asyncio import AsyncSession

from .consts import IDENTIFY_EVENT_NAME
from .enums import EventSource
from .models import Event
from .repository import (
    EventRepository,
    GroupRepository,
    PersonDistinctIdRepository,
    PersonGroupRepository,
    PersonRepository,
)

logger = logging.getLogger(__name__)

# --- utils ---


def _as_uuid(value: str | UUID) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _as_datetime(value: str | datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class PersonDistinctIdService:
    @staticmethod
    async def get_many(identities: set[tuple[UUID, str]], session: AsyncSession):
        return await PersonDistinctIdRepository.get_many(identities, session)

    @staticmethod
    async def create_many(rows: list[dict[str, Any]], session: AsyncSession) -> None:
        await PersonDistinctIdRepository.create_many(rows, session)

    @staticmethod
    async def reassign_person(
        source_id: UUID, target_id: UUID, session: AsyncSession
    ) -> None:
        await PersonDistinctIdRepository.reassign_person(source_id, target_id, session)


class PersonGroupService:
    @staticmethod
    async def add_many(rows: list[dict[str, Any]], session: AsyncSession) -> None:
        await PersonGroupRepository.add_many(rows, session)

    @staticmethod
    async def move_person_links(
        source_id: UUID, target_id: UUID, session: AsyncSession
    ) -> None:
        await PersonGroupRepository.move_person_links(source_id, target_id, session)

    @staticmethod
    async def move_person_links_many(
        person_merges: dict[UUID, UUID], session: AsyncSession
    ) -> None:
        await PersonGroupRepository.move_person_links_many(person_merges, session)


def _valid_identify_indexes(events: list[dict[str, Any]]) -> set[int]:
    """Drop identify edges that make an unordered batch ambiguous or cyclic."""
    by_tenant: dict[UUID, list[tuple[int, str, str]]] = defaultdict(list)
    for index, event in enumerate(events):
        alias = event.get("anon_distinct_id")
        target = event.get("distinct_id")
        if event.get("event_name") != IDENTIFY_EVENT_NAME or not alias:
            continue
        tenant_id = _as_uuid(event["tenant_id"])
        if not isinstance(alias, str) or not alias.strip() or alias == target:
            logger.warning("Skipping invalid $identify event at batch index %d", index)
            continue
        by_tenant[tenant_id].append((index, alias, target))

    valid: set[int] = set()
    for edges in by_tenant.values():
        # Identical duplicate links are harmless; any node participating in
        # multiple different links can form a chain, fork, or cycle.
        adjacency: dict[str, set[str]] = defaultdict(set)
        directed_edges = {(source, target) for _, source, target in edges}
        for index, source, target in edges:
            adjacency[source].add(target)
            adjacency[target].add(source)

        ambiguous_nodes = {
            node for node, neighbors in adjacency.items() if len(neighbors) > 1
        }
        for index, source, target in edges:
            # A reciprocal pair has only one neighbor per node in the
            # undirected graph, so detect this two-node cycle separately.
            is_two_node_cycle = (target, source) in directed_edges
            if (
                source not in ambiguous_nodes
                and target not in ambiguous_nodes
                and not is_two_node_cycle
            ):
                valid.add(index)
        for index, source, target in edges:
            if (
                source in ambiguous_nodes
                or target in ambiguous_nodes
                or (target, source) in directed_edges
            ):
                logger.warning(
                    "Skipping ambiguous $identify event at batch index %d", index
                )
    return valid


def invalid_identify_indexes(
    records: list[tuple[dict[str, Any], dict[str, Any]]],
) -> set[int]:
    """Return identify records that cannot be safely applied from this batch."""
    events = []
    for payload, _ in records:
        event = dict(payload)
        event["event_name"] = event.get("event", event.get("event_name"))
        event["tenant_id"] = _as_uuid(event["tenant_id"])
        events.append(event)

    valid = _valid_identify_indexes(events)
    return {
        index
        for index, event in enumerate(events)
        if event.get("event_name") == IDENTIFY_EVENT_NAME and index not in valid
    }


class PersonService:
    @staticmethod
    async def get_many(person_ids: set[UUID], session: AsyncSession):
        return await PersonRepository.get_many(person_ids, session)

    @staticmethod
    async def merge_profiles(
        updates: dict[UUID, dict[str, Any]], session: AsyncSession
    ) -> None:
        await PersonRepository.merge_profiles(updates, session)

    @staticmethod
    async def delete_many(person_ids: set[UUID], session: AsyncSession) -> None:
        await PersonRepository.delete_many(person_ids, session)

    @staticmethod
    async def resolve_many(
        identities: set[tuple[UUID, str]], session: AsyncSession
    ) -> dict[tuple[UUID, str], UUID]:
        mapping = await PersonDistinctIdService.get_many(identities, session)
        missing = identities - mapping.keys()
        if missing:
            pending_people = [
                ((tenant_id, distinct_id), uuid7())
                for tenant_id, distinct_id in missing
            ]
            new_people = [
                {
                    "id": person_id,
                    "tenant_id": identity[0],
                    "properties": {},
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
                for identity, person_id in pending_people
            ]
            await PersonRepository.create_many(new_people, session)
            # Pair each newly-created person to its identity, then let the
            # unique tenant/distinct constraint settle concurrent creators.
            pending = []
            for (tenant_id, distinct_id), person_id in pending_people:
                pending.append(
                    {
                        "id": uuid7(),
                        "tenant_id": tenant_id,
                        "person_id": person_id,
                        "distinct_id": distinct_id,
                        "created_at": datetime.now(timezone.utc),
                    }
                )
            await PersonDistinctIdService.create_many(pending, session)
            mapping = await PersonDistinctIdService.get_many(identities, session)
        return mapping

    @staticmethod
    async def apply_properties(
        events: list[dict[str, Any]],
        identity_map: dict[tuple[UUID, str], UUID],
        session: AsyncSession,
    ) -> None:
        property_events = [event for event in events if event.get("person_properties")]
        if not property_events:
            return

        person_ids = {
            identity_map[(_as_uuid(event["tenant_id"]), event["distinct_id"])]
            for event in property_events
        }
        property_updates: dict[UUID, dict[str, Any]] = {}
        people = await PersonRepository.get_many(person_ids, session)
        for event in property_events:
            properties = event.get("person_properties")
            if not properties:
                continue
            tenant_id = _as_uuid(event["tenant_id"])
            person_id = identity_map[(tenant_id, event["distinct_id"])]
            merged = property_updates.get(
                person_id, people[person_id].properties or {}
            ).copy()
            merged.update(properties)
            property_updates[person_id] = merged
        await PersonService.merge_profiles(property_updates, session)


class GroupService:
    @staticmethod
    async def merge_properties(
        updates: dict[UUID, dict[str, Any]], session: AsyncSession
    ) -> None:
        await GroupRepository.merge_properties(updates, session)

    @staticmethod
    async def resolve_many(identities: set[tuple[UUID, str]], session: AsyncSession):
        groups = await GroupRepository.get_many(identities, session)
        missing = identities - groups.keys()
        if missing:
            rows = [
                {
                    "id": uuid7(),
                    "tenant_id": tenant_id,
                    "group_key": key,
                    "properties": {},
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
                for tenant_id, key in missing
            ]
            await GroupRepository.create_many(rows, session)
            groups = await GroupRepository.get_many(identities, session)

        return groups


class EventService:
    @staticmethod
    async def process_batch(
        records: list[tuple[dict[str, Any], dict[str, Any]]], session: AsyncSession
    ) -> None:
        """Persist a Redpanda batch atomically; offsets are committed by the consumer."""
        events: list[dict[str, Any]] = []
        for payload, metadata in records:
            if not isinstance(payload, dict):
                raise ValueError("Redpanda event payload must be a JSON object")
            tenant_id = _as_uuid(payload["tenant_id"])
            event = dict(payload)
            event["tenant_id"] = tenant_id
            event["organization_id"] = _as_uuid(payload["organization_id"])
            event["api_key_id"] = _as_uuid(payload["api_key_id"])
            if event.get("session_id"):
                event["session_id"] = _as_uuid(event["session_id"])
            if event.get("ip_address"):
                event["ip_address"] = ipaddress.ip_interface(event["ip_address"])
            event["event_name"] = event.pop("event", event.get("event_name"))
            event["occurred_at"] = _as_datetime(
                event.pop("timestamp", event.get("occurred_at"))
            )
            event["received_at"] = _as_datetime(event.get("received_at"))
            event["created_at"] = event.get("created_at") or datetime.now(timezone.utc)
            event["raw_payload"] = event.get("raw_payload") or payload
            event["properties"] = event.get("properties") or {}
            event["source"] = EventSource.api
            event["id"] = uuid7()
            if not event.get("insert_id"):
                topic, partition, offset = (
                    metadata["topic"],
                    metadata["partition"],
                    metadata["offset"],
                )
                event["insert_id"] = str(
                    uuid5(NAMESPACE_URL, f"vortex-event:{topic}:{partition}:{offset}")
                )
            events.append(event)

        valid_identifies = _valid_identify_indexes(events)
        skipped = {
            index
            for index, event in enumerate(events)
            if event.get("event_name") == IDENTIFY_EVENT_NAME
            and index not in valid_identifies
        }
        processable = [event for i, event in enumerate(events) if i not in skipped]
        identities: set[tuple[UUID, str]] = set()
        for event in processable:
            tenant_id = event["tenant_id"]
            identities.add((tenant_id, event["distinct_id"]))
            if event.get("event_name") == IDENTIFY_EVENT_NAME and event.get(
                "anon_distinct_id"
            ):
                identities.add((tenant_id, event["anon_distinct_id"]))

        person_map = await PersonService.resolve_many(identities, session)
        await EventService._merge_identified_people(processable, person_map, session)
        await PersonService.apply_properties(processable, person_map, session)

        group_identities = {
            (event["tenant_id"], event["group_key"])
            for event in processable
            if event.get("group_key")
        }
        groups = await GroupService.resolve_many(group_identities, session)
        group_property_updates: dict[UUID, dict[str, Any]] = {}
        for event in processable:
            tenant_id = event["tenant_id"]
            event["person_id"] = person_map[(tenant_id, event["distinct_id"])]
            if event.get("group_key"):
                group = groups[(tenant_id, event["group_key"])]
                event["group_id"] = group.id
                incoming = event.get("group_properties") or {}
                if incoming:
                    merged = group_property_updates.get(
                        group.id, group.properties or {}
                    ).copy()
                    merged.update(incoming)
                    group_property_updates[group.id] = merged
        await GroupService.merge_properties(group_property_updates, session)

        links = [
            {
                "id": uuid7(),
                "person_id": event["person_id"],
                "group_id": event["group_id"],
                "created_at": datetime.now(timezone.utc),
            }
            for event in processable
            if event.get("group_id")
        ]
        await PersonGroupService.add_many(links, session)

        # Remove transport-only fields before inserting into the events table.
        allowed_fields = set(Event.__table__.columns.keys())
        rows = [
            {key: value for key, value in event.items() if key in allowed_fields}
            for event in processable
        ]
        await EventRepository.insert_many(rows, session)

    @staticmethod
    async def _merge_identified_people(
        events: list[dict[str, Any]],
        person_map: dict[tuple[UUID, str], UUID],
        session: AsyncSession,
    ) -> None:
        identify_events = [
            event
            for event in events
            if event.get("event_name") == IDENTIFY_EVENT_NAME
            and event.get("anon_distinct_id")
        ]
        if not identify_events:
            return

        identify_pairs = [
            (
                person_map[(event["tenant_id"], event["anon_distinct_id"])],
                person_map[(event["tenant_id"], event["distinct_id"])],
            )
            for event in identify_events
        ]
        person_ids = {
            person_id
            for source_id, target_id in identify_pairs
            if source_id != target_id
            for person_id in (source_id, target_id)
        }
        if not person_ids:
            return
        people = await PersonService.get_many(person_ids, session)
        profile_updates: dict[UUID, dict[str, Any]] = {}
        person_merges: dict[UUID, UUID] = {}
        sources_by_target: dict[UUID, set[UUID]] = defaultdict(set)
        merged_sources: set[UUID] = set()
        identity_keys_by_person: dict[UUID, list[tuple[UUID, str]]] = defaultdict(list)
        for identity, person_id in person_map.items():
            identity_keys_by_person[person_id].append(identity)

        for event in identify_events:
            tenant_id = event["tenant_id"]
            source_id = person_map[(tenant_id, event["anon_distinct_id"])]
            target_id = person_map[(tenant_id, event["distinct_id"])]
            if source_id == target_id or source_id in merged_sources:
                continue

            source_properties = profile_updates.get(
                source_id, people[source_id].properties or {}
            )
            target_properties = profile_updates.get(
                target_id, people[target_id].properties or {}
            )
            profile_updates[target_id] = source_properties | target_properties

            # Keep merge destinations flattened so each table is reassigned once.
            previous_sources = sources_by_target.pop(source_id, set())
            for previous_source in previous_sources:
                person_merges[previous_source] = target_id
            sources_by_target[target_id].update(previous_sources)
            sources_by_target[target_id].add(source_id)
            person_merges[source_id] = target_id

            merged_sources.add(source_id)
            for identity in identity_keys_by_person.pop(source_id, []):
                person_map[identity] = target_id
                identity_keys_by_person[target_id].append(identity)

        if not person_merges:
            return

        await PersonService.merge_profiles(profile_updates, session)
        await PersonGroupService.move_person_links_many(person_merges, session)
        await EventRepository.reassign_people(person_merges, session)
        await PersonDistinctIdRepository.reassign_people(person_merges, session)
        await PersonService.delete_many(set(person_merges), session)
