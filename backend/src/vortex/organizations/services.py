from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import InviteMemberRequest, SignupRequest
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
)


class OrganizationService:
    @staticmethod
    async def signup(
        db_session: AsyncSession,
        signup_data: SignupRequest,
    ) -> OrganizationMembership:

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

        # return Membership Orm Object
        return membership

    @staticmethod
    async def invite_member(
        db_session: AsyncSession,
        payload: InviteMemberRequest,
        org_id: UUID,
        invited_by_user_id: UUID,
    ) -> OrganizationMembership:

        row = await MembershipRepository.get_invite_precheck_row(
            db_session=db_session, email=payload.email, org_id=org_id
        )

        if row is None:
            target_user = await UserService.create_user(
                db_session=db_session,
                user_data={
                    "email": payload.email,
                    "hashed_password": hash_password(payload.password),
                    "first_name": None,
                    "last_name": None,
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

        return new_membership

    @staticmethod
    async def get_by_slug(db_session: AsyncSession, slug: str) -> Organization:
        org = await OrganizationRepository.get_by_slug(db_session=db_session, slug=slug)
        if org is None:
            raise OrganizationNotFoundError(identifier=slug)
        return org


class MembershipService:
    @staticmethod
    async def create_membership(
        db_session: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        role: InviteMembershipRole,
        invited_by_user_id: UUID,
    ):

        new_membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            invited_by_user_id=invited_by_user_id,
        )

        await MembershipRepository.create_membership(
            db_session=db_session, instance=new_membership
        )
        return new_membership

    @staticmethod
    async def get_membership(
        db_session: AsyncSession, org_id: UUID, user_id: UUID
    ) -> OrganizationMembership:
        membership = await MembershipRepository.get_membership(
            db_session=db_session, org_id=org_id, user_id=user_id
        )
        if membership is None:
            raise NotAMemberError(org_id=org_id, user_id=user_id)
        return membership
