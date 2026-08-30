from datetime import datetime, timezone
from fastapi import APIRouter, Cookie, Response

from src.vortex.shared.database import DbSessionDep
from src.vortex.shared.responses import ApiResponse

from .dependencies import OptionalUserDep
from .services import AuthService
from .schemas import LoginRequest
from .exceptions import (
    InvalidCredentialsError,
    RefreshTokenExpiredError,
    RefreshTokenNotFoundError,
    RefreshTokenRevokedError,
    SessionWindowExceededError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_PATH = "/auth"


@router.post("/login")
async def login(payload: LoginRequest, db_session: DbSessionDep, response: Response):

    try:
        access_token, raw_refresh_token = await AuthService.login(
            db_session=db_session,
            org_slug=payload.org_slug,
            email=payload.email,
            plain_password=payload.password,
        )
    except InvalidCredentialsError:
        return ApiResponse.error(
            message="Invalid organization, email, or password", code=401
        )

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
        max_age=90 * 24 * 60 * 60,
    )
    return ApiResponse.success(
        message="Login successful", data={"access_token": access_token}
    )


@router.post("/refresh")
async def refresh(
    response: Response,
    db_session: DbSessionDep,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
):
    if refresh_token is None:
        return ApiResponse.error(message="No refresh token provided", code=401)

    try:
        access_token, new_raw_refresh_token, max_window_limit = (
            await AuthService.refresh(
                db_session=db_session, raw_refresh_token=refresh_token
            )
        )
    except (
        RefreshTokenNotFoundError,
        RefreshTokenRevokedError,
        SessionWindowExceededError,
        RefreshTokenExpiredError,
    ):
        response.delete_cookie(key="refresh_token", path=REFRESH_COOKIE_PATH)
        return ApiResponse.error(
            message="Session expired, please log in again", code=401
        )

    remaining_seconds = int(
        (max_window_limit - datetime.now(timezone.utc)).total_seconds()
    )

    # dont pass negative value to cookie expiry
    remaining_seconds = max(remaining_seconds, 0)

    response.set_cookie(
        key="refresh_token",
        value=new_raw_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
        max_age=remaining_seconds,  #
    )
    return ApiResponse.success(
        message="Token refreshed", data={"access_token": access_token}
    )


@router.post("/logout")
async def logout(
    response: Response,
    db_session: DbSessionDep,
    optional_user_data: OptionalUserDep,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
):
    # --- delete the cookie ---
    if refresh_token:
        response.delete_cookie(key="refresh_token", path=REFRESH_COOKIE_PATH)

    # --- mark refresh token as inactive and set jwt jti to blacklisted ---

    jti = optional_user_data.get("jti")
    exp = optional_user_data.get("exp")
    ttl_seconds = exp - int(datetime.now(timezone.utc).timestamp()) if exp else None

    await AuthService.logout(
        db_session=db_session,
        raw_refresh_token=refresh_token,
        jti=jti,
        ttl_seconds=ttl_seconds,
    )

    return ApiResponse.success(code=204)
