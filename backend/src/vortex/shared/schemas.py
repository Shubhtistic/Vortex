from __future__ import annotations
from typing import Any, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


# --- Schema of Global Api Response ---
class ApiResponseSchema(BaseModel):
    """Pydantic schema of global api response"""

    message: str
    status_code: int
    data: Optional[T] = None
    meta: Optional[dict[str, Any]] = None
