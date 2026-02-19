from fastapi import Depends
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

DbSessionDep = Annotated[AsyncSession, Depends(get_session)]
