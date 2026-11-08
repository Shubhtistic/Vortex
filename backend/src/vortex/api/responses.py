from typing import Any, Optional, TypeVar
import orjson
from fastapi.responses import Response

# --- placeholder type var ----
T = TypeVar("T")


# --- Global Response class ---
class ApiResponse(Response):
    """global api response class for entire project"""

    media_type = "application/json"

    def __init__(self, content: dict, status_code: int) -> None:
        super().__init__(content=content, status_code=status_code)

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content, default=str)

    @classmethod
    def success(
        cls,
        message: str = "Success",
        data: Optional[T] = None,
        code: int = 200,
        meta: Optional[dict] = None,
    ) -> ApiResponse:
        return cls(
            content={
                "message": message,
                "status_code": code,
                "data": data,
                "meta": meta,
            },
            status_code=code,
        )

    @classmethod
    def error(
        cls,
        message: str = "Something went wrong",
        code: int = 400,
        data: Optional[T] = None,
        meta: Optional[dict] = None,
    ) -> ApiResponse:
        return cls(
            content={
                "message": message,
                "status_code": code,
                "data": data,
                "meta": meta,
            },
            status_code=code,
        )
