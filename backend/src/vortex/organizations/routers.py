from fastapi import APIRouter

from src.vortex.shared.schemas import ApiResponseSchema
from src.vortex.shared.database import DbSessionDep, get_session_factory
from src.vortex.shared.responses import ApiResponse
from src.vortex.users.exceptions import UserAlreadyExistsError
from src.vortex.auth.dependencies import VerifiedAdminDep

from .services import OrganizationService
from .schemas import SignupRequest, InviteMemberRequest
from .exceptions import (
    OrganizationAlreadyExistsError,
    CannotInviteRootAccountError,
    UserAlreadyMemberError,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/signup", response_model=ApiResponseSchema)
async def signup(payload: SignupRequest):
    session_factory = get_session_factory()
    async with session_factory() as db_session:
        try:
            # payload auto validated
            result = await OrganizationService.signup(
                db_session=db_session, signup_data=payload
            )
            # commit
            await db_session.commit()

        except (OrganizationAlreadyExistsError, UserAlreadyExistsError):
            await db_session.rollback()
            return ApiResponse.error(
                message="Organization slug already taken / Email already taken",
                code=409,
            )

    return ApiResponse.success(
        message="Organization created",
        code=201,
        data={
            "organization_id": result.organization_id,
            "user_id": result.user_id,
        },
    )


@router.post("/invite", response_model=ApiResponseSchema)
async def invite_member(
    payload: InviteMemberRequest,
    current_user: VerifiedAdminDep,
    db_session: DbSessionDep,
):
    try:
        membership = await OrganizationService.invite_member(
            db_session=db_session,
            payload=payload,
            org_id=current_user.get("org_id"),
            invited_by_user_id=current_user.get("user_id"),
        )
    except (CannotInviteRootAccountError, UserAlreadyMemberError):
        return ApiResponse.error(
            message="Email already registered or insufficient permissions",
            code=409,
        )
    return ApiResponse.success(
        message="Member invited", code=201, data={"membership_id": str(membership.id)}
    )
