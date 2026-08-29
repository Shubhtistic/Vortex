from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from .repository import UserRepository
from .exceptions import UserAlreadyExistsError, UserNotFoundError


class UserService:
    @staticmethod
    async def create_user(db_session: AsyncSession, user_data: dict) -> User:

        # user_data validated + password already hashed by caller (auth/organizations service layer)

        if await UserRepository.check_by_email(
            db_session=db_session, email=user_data["email"]
        ):
            raise UserAlreadyExistsError(email=user_data["email"])

        new_user = await UserRepository.create_user(
            db_session=db_session, instance=User(**user_data)
        )
        return new_user
