from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import (
    InviteMemberRequest,
    MembershipRead,
    OrgMemberRead,
    OrganizationResponse,
    SignupRequest,
)
from src.vortex.users.services import UserService
from src.vortex.auth.password import hash_password
from .models import Organization, OrganizationMembership
from .enums import InviteMembershipRole, MembershipRole
from .repository import OrganizationRepository, MembershipRepository
from .exceptions import (
    OrganizationAlreadyExistsError,
    OrganizationNotFoundError,
    NotAMemberError,
    CannotInviteRootAccountError,
    UserAlreadyMemberError,
    UserCannotBeDeletedError,
)

logger = logging.getLogger(__name__)


class OrganizationService:
    @staticmethod
    async def signup(
        db_session: AsyncSession,
        signup_data: SignupRequest,
    ) -> dict:

        # step 1 -> slug must be free
        if await OrganizationRepository.check_by_slug(
            db_session=db_session, slug=signup_data.slug
        ):
            raise OrganizationAlreadyExistsError(slug=signup_data.slug)

        # org slug is free
        org = await OrganizationRepository.create_organization(
            db_session=db_session,
            instance=Organization(name=signup_data.org_name, slug=signup_data.slug),
        )

        # create an user -> email should not exist anywhere as any role (superuser / admin , etc)
        # !! send hashed password
        user = await UserService.create_user(
            db_session=db_session,
            user_data={
                "email": signup_data.email,
                "hashed_password": hash_password(signup_data.password),
                "first_name": signup_data.first_name,
                "last_name": signup_data.last_name,
            },
        )
        # raises useralreadyexists exception, let it propagate router will catch it

        membership = await MembershipRepository.create_membership(
            db_session=db_session,
            instance=OrganizationMembership(
                organization_id=org.id, user_id=user.id, role=MembershipRole.owner
            ),
        )
        logger.info("Organization signup completed")
        # return Membership Orm Object
        return MembershipRead.model_validate(membership).model_dump()

    @staticmethod
    async def invite_member(
        db_session: AsyncSession,
        payload: InviteMemberRequest,
        org_id: UUID,
        invited_by_user_id: UUID,
    ) -> dict:

        row = await MembershipRepository.get_invite_precheck_row(
            db_session=db_session, email=payload.email, org_id=org_id
        )

        if row is None:
            target_user = await UserService.create_user(
                db_session=db_session,
                user_data={
                    "email": payload.email,
                    "hashed_password": hash_password(payload.password),
                    "first_name": payload.first_name,
                    "last_name": payload.last_name,
                },
            )
            target_user_id = target_user.id

        else:
            if row.is_superuser_anywhere is not None:
                raise CannotInviteRootAccountError(email=payload.email)
            if row.already_member is not None:
                raise UserAlreadyMemberError(org_id=org_id, email=payload.email)

            target_user_id = row.user_id

        new_membership = await MembershipService.create_membership(
            db_session=db_session,
            organization_id=org_id,
            user_id=target_user_id,
            role=payload.role,
            invited_by_user_id=invited_by_user_id,
        )
        logger.info("Organization member invitation completed")
        return MembershipRead.model_validate(new_membership).model_dump()

    @staticmethod
    async def get_by_slug(db_session: AsyncSession, slug: str) -> Organization:
        org = await OrganizationRepository.get_by_slug(db_session=db_session, slug=slug)
        if org is None:
            logger.warning("Organization lookup failed: organization not found")
            raise OrganizationNotFoundError(identifier=slug)
        return org

    @staticmethod
    async def get_org_info_by_id(org_id: UUID, db_session: AsyncSession) -> dict:
        org = await OrganizationRepository.get_org_by_id(
            org_id=org_id, db_session=db_session
        )
        if not org:
            logger.warning("Organization lookup failed: organization not found")
            raise OrganizationNotFoundError(identifier=str(org_id))

        logger.info("Organization details fetched")
        return OrganizationResponse.model_validate(org).model_dump()


class MembershipService:
    @staticmethod
    async def create_membership(
        db_session: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        role: InviteMembershipRole,
        invited_by_user_id: UUID,
    ) -> OrganizationMembership:

        new_membership_instance = OrganizationMembership(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            invited_by_user_id=invited_by_user_id,
        )

        new_membership = await MembershipRepository.create_membership(
            db_session=db_session, instance=new_membership_instance
        )
        logger.info("Organization membership created")
        return new_membership

    @staticmethod
    async def get_active_membership(
        db_session: AsyncSession, org_id: UUID, user_id: UUID
    ) -> OrganizationMembership:
        membership = await MembershipRepository.get_active_membership(
            db_session=db_session, org_id=org_id, user_id=user_id
        )
        if membership is None:
            logger.warning("Membership lookup failed: active membership not found")
            raise NotAMemberError(org_id=org_id, user_id=user_id)
        return membership

    @staticmethod
    async def get_all_active_org_members(
        org_id: UUID, db_session: AsyncSession, limit: int, page_num: int
    ) -> tuple[list[dict], int]:
        offset = (page_num - 1) * limit

        memberships, total_count = await MembershipRepository.get_all_active_members(
            org_id, db_session, offset, limit
        )
        if not total_count:
            logger.debug("No active organization members found")
            return [], 0

        users_by_id = await UserService.get_users_by_ids(
            db_session=db_session, user_ids=[m.user_id for m in memberships]
        )

        data = [
            OrgMemberRead(
                user_id=m.user_id,
                role=m.role,
                email=users_by_id[m.user_id].email,
                first_name=users_by_id[m.user_id].first_name,
                last_name=users_by_id[m.user_id].last_name,
            ).model_dump()
            for m in memberships
            if m.user_id in users_by_id
        ]
        return data, total_count

    @staticmethod
    async def deactivate_member(
        db_session: AsyncSession, org_id: UUID, target_user_id: UUID
    ) -> UUID | str:
        if deleted_id := await MembershipRepository.deactivate_member(
            db_session=db_session, org_id=org_id, user_id=target_user_id
        ):
            logger.info("Organization membership deactivated")
            return deleted_id

        logger.warning("Organization membership deactivation failed")
        raise UserCannotBeDeletedError
