from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.vortex.shared.database import create, execute_query, get_one_by_query
from src.vortex.shared.redis_client import get_redis

from .models import RefreshTokens


class RefreshTokenRepository:
    @staticmethod
    async def create(
        db_session: AsyncSession, instance: RefreshTokens
    ) -> RefreshTokens:
        return await create(instance=instance, db_session=db_session)

    @staticmethod
    async def get_by_hash(
        db_session: AsyncSession, token_hash: str
    ) -> Optional[RefreshTokens]:
        """get a refresh token by hash"""

        qry = select(RefreshTokens).where(RefreshTokens.hashed_token == token_hash)
        return await get_one_by_query(qry, db_session)

    @staticmethod
    async def revoke(db_session: AsyncSession, hashed_token: str, revoked_at: datetime):
        """set a token as revoked"""

        qry = (
            update(RefreshTokens)
            .where(RefreshTokens.hashed_token == hashed_token)
            .values(is_revoked=True, revoked_at=revoked_at)
        )
        return await execute_query(query=qry, db_session=db_session)

    @staticmethod
    async def update(
        db_session: AsyncSession,
        token_id: UUID,
        hashed_token: str,
        expires_at: datetime,
        role: str,
    ) -> None:
        """update a refresh token row in place after a successful rotation"""
        stmt = (
            update(RefreshTokens)
            .where(RefreshTokens.id == token_id)
            .values(
                hashed_token=hashed_token,
                expires_at=expires_at,
                role=role,
            )
        )
        await execute_query(query=stmt, db_session=db_session)


class JwtRepository:
    @staticmethod
    async def add_jti_to_blacklist(jti: str, ttl_seconds: int) -> None:

        if ttl_seconds <= 0:
            return
        redis = get_redis()
        await redis.setex(f"blacklist:jti:{jti}", ttl_seconds, "1")

    @staticmethod
    async def check_jti_blacklist(jti: str) -> bool:
        """Returns True if this jti has been blacklisted (e.g. via logout)."""

        redis = get_redis()
        result = await redis.get(f"blacklist:jti:{jti}")
        return result is not None
