from datetime import datetime, timedelta, timezone
import hashlib, secrets
from typing import Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.vortex.users.services import UserService
from src.vortex.users.exceptions import UserNotFoundError
from src.vortex.organizations.services import OrganizationService, MembershipService
from src.vortex.organizations.exceptions import (
    OrganizationNotFoundError,
    NotAMemberError,
)

from .jwt import create_access_token
from .password import verify_password
from .models import RefreshTokens
from .repository import RefreshTokenRepository, JwtRepository
from .exceptions import (
    InvalidCredentialsError,
    RefreshTokenExpiredError,
    RefreshTokenNotFoundError,
    RefreshTokenRevokedError,
    SessionWindowExceededError,
)


class AuthService:
    @staticmethod
    async def login(
        db_session: AsyncSession, org_slug: str, email: str, plain_password: str
    ) -> tuple[str, str]:
        # step 1 -> Organization table: slug -> org_id
        try:
            org = await OrganizationService.get_by_slug(
                db_session=db_session, slug=org_slug
            )
        except OrganizationNotFoundError:
            raise InvalidCredentialsError(email=email)  # generic on purpose

        # step 2 -> User table: email -> user row (+ password check)
        try:
            user = await UserService.get_by_email(db_session=db_session, email=email)
        except UserNotFoundError:
            raise InvalidCredentialsError(email=email)

        if not verify_password(plain_password, user.hashed_password):
            raise InvalidCredentialsError(email=email)

        # step 3 -> OrganizationMembership table: (org_id, user_id) -> role
        try:
            membership = await MembershipService.get_membership(
                db_session=db_session, org_id=org.id, user_id=user.id
            )
        except NotAMemberError:
            raise InvalidCredentialsError(email=email)

        # step 4 -> return access_token and refresh_tokens
        access_token = create_access_token(
            user_id=user.id, org_id=org.id, role=membership.role
        )
        refresh_token = await RefreshTokenService.create(
            db_session=db_session, user_id=user.id, org_id=org.id, role=membership.role
        )

        return access_token, refresh_token

    @staticmethod
    async def refresh(
        db_session: AsyncSession, raw_refresh_token: str
    ) -> tuple[str, str, datetime]:
        """try to rotate a refresh token and if succeeds send (access_token, refresh_token)"""

        # exceptions will be raised, let router catch them
        raw_refresh_token, membership, max_window_limit = (
            await RefreshTokenService.rotate(
                db_session=db_session, raw_refresh_token=raw_refresh_token
            )
        )

        access_token = create_access_token(
            user_id=membership.user_id,
            org_id=membership.organization_id,
            role=membership.role,
        )

        return access_token, raw_refresh_token, max_window_limit

    @staticmethod
    async def logout(
        db_session: AsyncSession,
        raw_refresh_token: Optional[str] = None,
        jti: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ):

        # set the refresh token as revoked
        if raw_refresh_token:
            await RefreshTokenRepository.revoke(
                db_session=db_session,
                hashed_token=RefreshTokenService.hash_token(raw_refresh_token),
                revoked_at=datetime.now(timezone.utc),
            )

        # set the jwt as blacklisted
        if jti and ttl_seconds:
            await JwtRepository.add_jti_to_blacklist(jti=jti, ttl_seconds=ttl_seconds)

        return None


class RefreshTokenService:

    SLIDING_WINDOW = timedelta(days=7)
    MAX_SESSION_WINDOW = timedelta(days=90)

    @staticmethod
    def calculate_next_expiry(now: datetime, max_window_limit: datetime) -> datetime:
        """slide the expiry using sliding window, does not exceed max_window limit"""

        return min(now + RefreshTokenService.SLIDING_WINDOW, max_window_limit)

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()

    @staticmethod
    def generate_refresh_token() -> tuple[str, str]:
        """return raw and hashed refresh token"""
        raw_token = secrets.token_urlsafe(32)
        return raw_token, RefreshTokenService.hash_token(raw_token)

    @staticmethod
    async def create(
        db_session: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        role: str,
    ) -> str:
        """create a refresh token and save in db"""

        now = datetime.now(timezone.utc)
        raw_token, token_hash = RefreshTokenService.generate_refresh_token()

        new_refresh_token = RefreshTokens(
            user_id=user_id,
            org_id=org_id,
            role=role,
            hashed_token=token_hash,
            max_window_limit=now + RefreshTokenService.MAX_SESSION_WINDOW,
            expires_at=now + RefreshTokenService.SLIDING_WINDOW,
        )

        await RefreshTokenRepository.create(
            db_session=db_session, instance=new_refresh_token
        )

        return raw_token

    @staticmethod
    async def rotate(
        db_session: AsyncSession,
        raw_refresh_token: str,
    ) -> tuple[str, Any, datetime]:
        """called when refreshing a token,if under max_session limit -> updated"""

        now = datetime.now(timezone.utc)

        hashed_token = RefreshTokenService.hash_token(raw_refresh_token)

        existing_token = await RefreshTokenRepository.get_by_hash(
            db_session, hashed_token
        )
        if existing_token is None:
            raise RefreshTokenNotFoundError

        if existing_token.is_revoked:
            raise RefreshTokenRevokedError

        if now >= existing_token.max_window_limit:
            raise SessionWindowExceededError

        if now >= existing_token.expires_at:
            raise RefreshTokenExpiredError

        membership = await MembershipService.get_membership(
            db_session=db_session,
            org_id=existing_token.org_id,
            user_id=existing_token.user_id,
        )
        if (not membership) or (not membership.is_active):
            raise RefreshTokenExpiredError

        new_expires_at = RefreshTokenService.calculate_next_expiry(
            now=now,
            max_window_limit=existing_token.max_window_limit,
        )

        new_raw_token, new_hashed_token = RefreshTokenService.generate_refresh_token()

        await RefreshTokenRepository.update(
            db_session=db_session,
            token_id=existing_token.id,
            hashed_token=new_hashed_token,
            expires_at=new_expires_at,
            role=membership.role.value,
        )

        return new_raw_token, membership, existing_token.max_window_limit
