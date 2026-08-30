from typing import Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import OperationalError

from src.vortex.shared.database import DbSessionDep
from src.vortex.organizations.repository import MembershipRepository
from src.vortex.organizations.enums import MembershipRole
from .jwt import decode_and_verify_token
from .exceptions import ExpiredSignatureError, InvalidTokenError, UnexpectedJwtError

bearer_scheme = HTTPBearer()


async def current_user_dep(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict:
    """tier 1 -> decode + verify JWT signature/expiry only. No DB hit."""
    try:
        claims = decode_and_verify_token(credentials.credentials)
    except (ExpiredSignatureError, InvalidTokenError, UnexpectedJwtError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return claims


async def optional_current_user_dep(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict:
    """currently only for logout"""
    try:
        claims = decode_and_verify_token(credentials.credentials)
    except (ExpiredSignatureError, InvalidTokenError, UnexpectedJwtError):
        return {}
    return claims


async def _get_verified_membership(current_user: dict, db_session: DbSessionDep):
    """Shared DB-verification step for tier 2 and tier 3 deps."""
    try:
        user_id = UUID(current_user["user_id"])
        org_id = UUID(current_user["org_id"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims",
        )

    try:
        membership = await MembershipRepository.get_membership(
            db_session=db_session, org_id=org_id, user_id=user_id
        )
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable, please try again shortly",
        )

    if membership is None or not membership.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an active member of this organization",
        )

    return membership


async def verified_admin_dep(
    current_user: Annotated[dict, Depends(current_user_dep)],
    db_session: DbSessionDep,
) -> dict:
    """Tier 2 — DB-verified. Allows admin or owner"""
    membership = await _get_verified_membership(current_user, db_session)

    if membership.role not in (MembershipRole.admin, MembershipRole.owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner role required",
        )
    return current_user


async def verified_owner_dep(
    current_user: Annotated[dict, Depends(current_user_dep)],
    db_session: DbSessionDep,
) -> dict:
    """Tier 3 -> owner only"""

    membership = await _get_verified_membership(current_user, db_session)

    if membership.role != MembershipRole.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner role required",
        )
    return current_user


# --- Dependancies ---

CurrentUserDep = Annotated[dict, Depends(current_user_dep)]
VerifiedAdminDep = Annotated[dict, Depends(verified_admin_dep)]
VerifiedOwnerDep = Annotated[dict, Depends(verified_admin_dep)]
OptionalUserDep = Annotated[dict, Depends(optional_current_user_dep)]
