from typing import Optional
from uuid import UUID
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.vortex.organizations.enums import MembershipRole

from .models import Organization, OrganizationMembership
from src.vortex.shared.database import (
    check_exists,
    create,
    execute_query,
    get_all,
    get_one_by_query,
)


class OrganizationRepository:
    @staticmethod
    async def check_by_slug(db_session: AsyncSession, slug: str) -> bool:
        return await check_exists(
            model=Organization, db_session=db_session, filters={"slug": slug}
        )

    @staticmethod
    async def create_organization(
        db_session: AsyncSession, instance: Organization
    ) -> Organization:
        return await create(instance=instance, db_session=db_session)

    @staticmethod
    async def get_by_slug(db_session: AsyncSession, slug: str) -> Organization | None:

        stmt = select(Organization).where(
            Organization.slug == slug, Organization.is_active == True
        )

        return await get_one_by_query(stmt, db_session)

    @staticmethod
    async def get_org_by_id(
        org_id: UUID, db_session: AsyncSession
    ) -> Optional[Organization]:
        qry = select(Organization).where(
            Organization.id == org_id, Organization.is_active == True
        )
        return await get_one_by_query(qry, db_session)


class MembershipRepository:
    @staticmethod
    async def create_membership(
        db_session: AsyncSession, instance: OrganizationMembership
    ) -> OrganizationMembership:
        return await create(instance=instance, db_session=db_session)

    @staticmethod
    async def get_active_membership(
        db_session: AsyncSession, org_id: UUID, user_id: UUID
    ) -> OrganizationMembership | None:
        stmt = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.is_active == True,
        )

        return await get_one_by_query(stmt, db_session)

    @staticmethod
    async def has_active_owner_membership(
        db_session: AsyncSession, user_id: UUID
    ) -> bool:
        return await check_exists(
            model=OrganizationMembership,
            db_session=db_session,
            filters={
                "user_id": user_id,
                "role": MembershipRole.owner,
                "is_active": True,
            },
        )

    @staticmethod
    async def get_all_active_members(org_id: UUID, db_session, offset: int, limit: int):
        """get all active members"""
        count_q = (
            select(func.count())
            .select_from(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == org_id,
                OrganizationMembership.is_active == True,
            )
        )

        total_count = (
            await execute_query(query=count_q, db_session=db_session)
        ).scalar_one()

        q = (
            select(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == org_id,
                OrganizationMembership.is_active == True,
            )
            .order_by(OrganizationMembership.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        data = await get_all(stmt=q, db_session=db_session)

        return data, total_count

    @staticmethod
    async def deactivate_member(
        db_session: AsyncSession, org_id: UUID, user_id: UUID
    ) -> UUID | str:
        stmt = (
            update(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == org_id,
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_active == True,
                OrganizationMembership.role != MembershipRole.owner,
            )
            .values(is_active=False)
            .returning(OrganizationMembership.user_id)
        )
        result = await execute_query(stmt, db_session=db_session)
        return result.scalar_one_or_none()
