from uuid import UUID
from sqlalchemy import literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.vortex.users.models import User
from src.vortex.organizations.enums import MembershipRole

from .models import Organization, OrganizationMembership
from src.vortex.shared.database import check_exists, create, execute_query, get_one_by_query


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

        stmt = select(Organization).where(Organization.slug == slug, Organization.is_active==True)

        return get_one_by_query(stmt,db_session)


class MembershipRepository:
    @staticmethod
    async def create_membership(
        db_session: AsyncSession, instance: OrganizationMembership
    ) -> OrganizationMembership:
        return await create(instance=instance, db_session=db_session)

    @staticmethod
    async def get_membership(
        db_session: AsyncSession, org_id: UUID, user_id: UUID
    ) -> OrganizationMembership | None:
        stmt = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == user_id,
        )
        
        return get_one_by_query(stmt,db_session)

    @staticmethod
    async def get_invite_precheck_row(
        db_session: AsyncSession, email: str, org_id: UUID
    ):
        """
        One round trip: resolves a user by email and, in the same query,
        flags whether they're an active owner anywhere and an active
        member of this specific org. Returns a Row or None if no user
        matches the email.
        """
        is_owner_subq = (
            select(literal_column("1"))
            .select_from(OrganizationMembership)
            .where(
                OrganizationMembership.user_id == User.id,
                OrganizationMembership.role == MembershipRole.owner,
                OrganizationMembership.is_active == True,
            )
            .limit(1)
            .scalar_subquery()
        )
        already_member_subq = (
            select(literal_column("1"))
            .select_from(OrganizationMembership)
            .where(
                OrganizationMembership.user_id == User.id,
                OrganizationMembership.organization_id == org_id,
                OrganizationMembership.is_active == True,
            )
            .limit(1)
            .scalar_subquery()
        )

        stmt = select(
            User.id.label("user_id"),
            is_owner_subq.label("is_superuser_anywhere"),
            already_member_subq.label("already_member"),
        ).where(User.email == email)

        result = await execute_query(stmt=stmt, db_session=db_session)
        return result.one_or_none()
