from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from src.vortex.shared.database import check_exists, create, get_one_by_query


class UserRepository:
    @staticmethod
    async def check_by_email(db_session: AsyncSession, email: str) -> bool:
        return await check_exists(
            model=User, db_session=db_session, filters={"email": email}
        )

    @staticmethod
    async def create_user(db_session: AsyncSession, instance: User) -> User:
        return await create(instance=instance, db_session=db_session)

    @staticmethod
    async def get_by_email(db_session: AsyncSession, email: str) -> Optional[User]:
        qry = select(User).where(User.email == email, User.is_active == True)

        return await get_one_by_query(qry, db_session)
