from datetime import datetime, timezone
from itertools import islice
from typing import Any, Iterable, TypeVar
from uuid import UUID, uuid7

from sqlalchemy import case, delete, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.vortex.shared.database import execute_query

from .consts import EVENTS_INSERT_CHUNK_SIZE
from .models import Event, Group, Person, PersonDistinctId, PersonGroup

MAX_BIND_PARAMETERS = 32_767
T = TypeVar("T")


def _chunks(values: Iterable[T], chunk_size: int) -> Iterable[list[T]]:
    iterator = iter(values)
    while chunk := list(islice(iterator, chunk_size)):
        yield chunk


def _safe_insert_chunk_size(model: Any, preferred_size: int) -> int:
    # SQLAlchemy emits one bind parameter per populated column in each row.
    column_count = len(model.__table__.columns)
    return min(preferred_size, MAX_BIND_PARAMETERS // column_count)


def _safe_mapping_chunk_size(bind_parameters_per_item: int = 3) -> int:
    # CASE updates also bind each mapping key in the WHERE IN clause.
    return MAX_BIND_PARAMETERS // bind_parameters_per_item


class EventRepository:
    @staticmethod
    async def insert_many(rows: list[dict[str, Any]], session: AsyncSession) -> None:
        if not rows:
            return

        # Drop duplicates in this batch before PostgreSQL checks the same unique key.
        unique_rows = []
        seen_insert_ids: set[tuple[UUID, str]] = set()
        for row in rows:
            insert_id = row.get("insert_id")
            if insert_id is not None:
                unique_key = (row["tenant_id"], insert_id)
                if unique_key in seen_insert_ids:
                    continue
                seen_insert_ids.add(unique_key)
            unique_rows.append(row)

        # Keep each statement below PostgreSQL's bind-parameter limit.
        chunk_size = _safe_insert_chunk_size(Event, EVENTS_INSERT_CHUNK_SIZE)
        for batch in _chunks(unique_rows, chunk_size):
            stmt = (
                pg_insert(Event)
                .values(batch)
                .on_conflict_do_nothing(index_elements=["tenant_id", "insert_id"])
            )
            await execute_query(query=stmt, db_session=session)

    @staticmethod
    async def reassign_person(
        source_id: UUID, target_id: UUID, session: AsyncSession
    ) -> None:
        await EventRepository.reassign_people({source_id: target_id}, session)

    @staticmethod
    async def reassign_people(
        person_merges: dict[UUID, UUID], session: AsyncSession
    ) -> None:
        person_merges = {
            source_id: target_id
            for source_id, target_id in person_merges.items()
            if source_id != target_id
        }
        if not person_merges:
            return
        for batch in _chunks(
            person_merges.items(), _safe_mapping_chunk_size()
        ):
            mapping = dict(batch)
            stmt = (
                update(Event)
                .where(Event.person_id.in_(mapping))
                .values(person_id=case(mapping, value=Event.person_id))
            )
            await execute_query(query=stmt, db_session=session)


class PersonRepository:
    @staticmethod
    async def get_many(
        person_ids: set[UUID], session: AsyncSession
    ) -> dict[UUID, Person]:
        if not person_ids:
            return {}
        people: dict[UUID, Person] = {}
        for batch in _chunks(person_ids, MAX_BIND_PARAMETERS):
            stmt = (
                select(Person)
                .where(Person.id.in_(batch))
                .execution_options(populate_existing=True)
            )
            result = await execute_query(query=stmt, db_session=session)
            people.update({person.id: person for person in result.scalars()})
        return people

    @staticmethod
    async def create_many(rows: list[dict[str, Any]], session: AsyncSession) -> None:
        chunk_size = _safe_insert_chunk_size(Person, 5000)
        for batch in _chunks(rows, chunk_size):
            stmt = pg_insert(Person).values(batch).on_conflict_do_nothing()
            await execute_query(query=stmt, db_session=session)

    @staticmethod
    async def merge_profiles(
        updates: dict[UUID, dict[str, Any]], session: AsyncSession
    ) -> None:
        if not updates:
            return
        for batch in _chunks(updates.items(), _safe_mapping_chunk_size()):
            mapping = dict(batch)
            stmt = (
                update(Person)
                .where(Person.id.in_(mapping))
                .values(
                    properties=case(
                        mapping, value=Person.id, else_=Person.properties
                    ),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await execute_query(query=stmt, db_session=session)

    @staticmethod
    async def delete_many(person_ids: set[UUID], session: AsyncSession) -> None:
        for batch in _chunks(person_ids, MAX_BIND_PARAMETERS):
            stmt = delete(Person).where(Person.id.in_(batch))
            await execute_query(query=stmt, db_session=session)


class PersonDistinctIdRepository:
    @staticmethod
    async def get_many(
        identities: set[tuple[UUID, str]], session: AsyncSession
    ) -> dict[tuple[UUID, str], UUID]:
        if not identities:
            return {}
        found: dict[tuple[UUID, str], UUID] = {}
        for batch in _chunks(identities, MAX_BIND_PARAMETERS // 2):
            stmt = select(
                PersonDistinctId.tenant_id,
                PersonDistinctId.distinct_id,
                PersonDistinctId.person_id,
            ).where(
                tuple_(PersonDistinctId.tenant_id, PersonDistinctId.distinct_id).in_(
                    batch
                )
            )
            result = await execute_query(query=stmt, db_session=session)
            found.update(
                {(row.tenant_id, row.distinct_id): row.person_id for row in result}
            )
        return found

    @staticmethod
    async def create_many(rows: list[dict[str, Any]], session: AsyncSession) -> None:
        # Acquire unique-index locks in a consistent order across concurrent
        # processors to avoid deadlocks when batches overlap.
        rows = sorted(
            rows, key=lambda row: (str(row["tenant_id"]), row["distinct_id"])
        )
        chunk_size = _safe_insert_chunk_size(PersonDistinctId, 5000)
        for batch in _chunks(rows, chunk_size):
            stmt = (
                pg_insert(PersonDistinctId)
                .values(batch)
                .on_conflict_do_nothing(index_elements=["tenant_id", "distinct_id"])
            )
            await execute_query(query=stmt, db_session=session)

    @staticmethod
    async def reassign_person(
        source_id: UUID, target_id: UUID, session: AsyncSession
    ) -> None:
        await PersonDistinctIdRepository.reassign_people(
            {source_id: target_id}, session
        )

    @staticmethod
    async def reassign_people(
        person_merges: dict[UUID, UUID], session: AsyncSession
    ) -> None:
        person_merges = {
            source_id: target_id
            for source_id, target_id in person_merges.items()
            if source_id != target_id
        }
        if not person_merges:
            return
        for batch in _chunks(person_merges.items(), _safe_mapping_chunk_size()):
            mapping = dict(batch)
            stmt = (
                update(PersonDistinctId)
                .where(PersonDistinctId.person_id.in_(mapping))
                .values(person_id=case(mapping, value=PersonDistinctId.person_id))
            )
            await execute_query(query=stmt, db_session=session)


class GroupRepository:
    @staticmethod
    async def get_many(
        identities: set[tuple[UUID, str]], session: AsyncSession
    ) -> dict[tuple[UUID, str], Group]:
        if not identities:
            return {}
        groups: dict[tuple[UUID, str], Group] = {}
        for batch in _chunks(identities, MAX_BIND_PARAMETERS // 2):
            stmt = select(Group).where(
                tuple_(Group.tenant_id, Group.group_key).in_(batch)
            )
            result = await execute_query(query=stmt, db_session=session)
            groups.update(
                {(group.tenant_id, group.group_key): group for group in result.scalars()}
            )
        return groups

    @staticmethod
    async def create_many(rows: list[dict[str, Any]], session: AsyncSession) -> None:
        chunk_size = _safe_insert_chunk_size(Group, 5000)
        for batch in _chunks(rows, chunk_size):
            stmt = (
                pg_insert(Group)
                .values(batch)
                .on_conflict_do_nothing(index_elements=["tenant_id", "group_key"])
            )
            await execute_query(query=stmt, db_session=session)

    @staticmethod
    async def merge_properties(
        updates: dict[UUID, dict[str, Any]], session: AsyncSession
    ) -> None:
        if not updates:
            return
        for batch in _chunks(updates.items(), _safe_mapping_chunk_size()):
            mapping = dict(batch)
            stmt = (
                update(Group)
                .where(Group.id.in_(mapping))
                .values(
                    properties=case(mapping, value=Group.id, else_=Group.properties),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await execute_query(query=stmt, db_session=session)


class PersonGroupRepository:
    @staticmethod
    async def add_many(rows: list[dict[str, Any]], session: AsyncSession) -> None:
        unique_rows: dict[tuple[UUID, UUID], dict[str, Any]] = {}
        for row in rows:
            unique_rows.setdefault((row["person_id"], row["group_id"]), row)
        rows = list(unique_rows.values())
        chunk_size = _safe_insert_chunk_size(PersonGroup, 5000)
        for batch in _chunks(rows, chunk_size):
            stmt = (
                pg_insert(PersonGroup)
                .values(batch)
                .on_conflict_do_nothing(index_elements=["person_id", "group_id"])
            )
            await execute_query(query=stmt, db_session=session)

    @staticmethod
    async def move_person_links(
        source_id: UUID, target_id: UUID, session: AsyncSession
    ) -> None:
        await PersonGroupRepository.move_person_links_many(
            {source_id: target_id}, session
        )

    @staticmethod
    async def move_person_links_many(
        person_merges: dict[UUID, UUID], session: AsyncSession
    ) -> None:
        person_merges = {
            source_id: target_id
            for source_id, target_id in person_merges.items()
            if source_id != target_id
        }
        if not person_merges:
            return
        links = []
        for batch in _chunks(person_merges, MAX_BIND_PARAMETERS):
            stmt = select(PersonGroup.person_id, PersonGroup.group_id).where(
                PersonGroup.person_id.in_(batch)
            )
            links.extend(await execute_query(query=stmt, db_session=session))
        target_links = {
            (person_merges[source_id], group_id)
            for source_id, group_id in links
        }
        rows = [
            {
                "id": uuid7(),
                "person_id": person_id,
                "group_id": group_id,
                "created_at": datetime.now(timezone.utc),
            }
            for person_id, group_id in target_links
        ]
        await PersonGroupRepository.add_many(rows, session)
        for batch in _chunks(person_merges, MAX_BIND_PARAMETERS):
            stmt = delete(PersonGroup).where(PersonGroup.person_id.in_(batch))
            await execute_query(query=stmt, db_session=session)
