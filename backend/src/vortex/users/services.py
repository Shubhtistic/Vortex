from typing import Optional
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.vortex.users.schemas import UserResponse

from .models import User
from .repository import UserRepository
from .exceptions import UserAlreadyExistsError, UserNotFoundError

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    async def create_user(db_session: AsyncSession, user_data: dict) -> User:

        # user_data validated + password already hashed by caller (auth/organizations service layer)

        if await UserRepository.check_by_email(
            db_session=db_session, email=user_data["email"]
        ):
            logger.warning("User creation rejected: email already exists")
            raise UserAlreadyExistsError(email=user_data["email"])

        new_user = await UserRepository.create_user(
            db_session=db_session, instance=User(**user_data)
        )
        logger.info("User created")
        return new_user

    @staticmethod
    async def get_by_email(db_session: AsyncSession, email: str) -> Optional[User]:

        if not (
            user := await UserRepository.get_by_email(
                db_session=db_session, email=email
            )
        ):
            logger.debug("User lookup by email returned no active user")
            raise UserNotFoundError(identifier=email)

        return user

    @staticmethod
    async def get_users_by_ids(
        db_session: AsyncSession, user_ids: list[UUID]
    ) -> dict[UUID, UserResponse]:

        users = await UserRepository.get_by_ids(
            db_session=db_session, user_ids=user_ids
        )
        logger.debug("Users fetched by ID list", extra={"count": len(users)})
        return {u.id: UserResponse.model_validate(u) for u in users}

    @staticmethod
    async def get_user_info_by_id(user_id: UUID, db_session: AsyncSession) -> dict:
        user = await UserRepository.get_user_by_id(
            user_id=user_id, db_session=db_session
        )
        if not user:
            logger.debug("User lookup by ID returned no active user")
            raise UserNotFoundError(identifier=str(user_id))

        logger.info("User details fetched")
        return UserResponse.model_validate(user).model_dump()
