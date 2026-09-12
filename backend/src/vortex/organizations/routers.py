from uuid import UUID

from fastapi import APIRouter, Query

from src.vortex.shared.database import DbSessionDep, get_session_factory
from src.vortex.shared.responses import ApiResponse
from src.vortex.users.exceptions import UserAlreadyExistsError
from src.vortex.auth.dependencies import (
    CurrentUserDep,
    VerifiedAdminDep,
    VerifiedOwnerDep,
)

from .services import MembershipService, OrganizationService
from .schemas import SignupRequest, InviteMemberRequest
from .exceptions import (
    OrganizationAlreadyExistsError,
    CannotInviteRootAccountError,
    OrganizationNotFoundError,
    UserAlreadyMemberError,
    UserCannotBeDeletedError,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/signup")
async def signup(payload: SignupRequest):
    session_factory = get_session_factory()
    async with session_factory() as db_session:
        try:
            # payload auto validated
            membership_dict = await OrganizationService.signup(
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
        data=membership_dict,
    )


@router.post("/invite")
async def invite_member(
    payload: InviteMemberRequest,
    current_user: VerifiedAdminDep,
    db_session: DbSessionDep,
):
    try:
        membership_dict_data = await OrganizationService.invite_member(
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
        message="Member invited",
        code=201,
        data=membership_dict_data,
    )


@router.get("/me")
async def get_org_info(db_session: DbSessionDep, current_user: CurrentUserDep):
    try:
        data = await OrganizationService.get_org_info_by_id(
            org_id=current_user.get("org_id"), db_session=db_session
        )
    except OrganizationNotFoundError:
        return ApiResponse.error(message="Organization not found", code=404)

    return ApiResponse.success(message="Organization fetched Successfully", data=data)


@router.get("/members")
async def get_all_members(
    db_session: DbSessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(10, ge=1, le=50),
    page_num: int = Query(1, ge=1),
):
    org_id = current_user["org_id"]

    data, total_count = await MembershipService.get_all_active_org_members(
        org_id=org_id,
        db_session=db_session,
        limit=limit,
        page_num=page_num,
    )
    total_pages = (total_count + limit - 1) // limit if total_count else 0

    return ApiResponse.success(
        message="org members fetched",
        data=data,
        meta={
            "limit": limit,
            "page_num": page_num,
            "total_count": total_count,
            "total_pages": total_pages,
        },
    )


@router.delete("/members/{user_id}")
async def deactivate_member(
    user_id: UUID,
    db_session: DbSessionDep,
    current_user: VerifiedOwnerDep,
):

    try:

        deleted_id = await MembershipService.deactivate_member(
            db_session=db_session,
            org_id=current_user["org_id"],
            target_user_id=user_id,
        )

    except UserCannotBeDeletedError:
        return ApiResponse.error(message="This User Could not be deleted be Deleted")

    return ApiResponse.success(
        message="member deactivated", data={"user_id": deleted_id}
    )
