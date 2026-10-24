import logging
import time

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from src.vortex.shared.config import get_settings

logger = logging.getLogger("app.request")


async def log_requests(request: Request, call_next):
    # only handle actual HTTP requests; FastAPI's middleware decorator handles HTTP requests only
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request failed",
            extra={"method": request.method, "path": request.url.path},
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )
    response.headers["X-Processing-Time-Ms"] = f"{duration_ms:.2f}"
    return response


class CORSMiddlewareWithSettings(CORSMiddleware):
    def __init__(self, app):
        # Keep CORS settings in one place alongside the other middleware definitions.
        settings = get_settings()
        super().__init__(
            app,
            allow_origins=settings.cors.allowed_origins,
            allow_methods=settings.cors.allowed_methods,
            allow_headers=settings.cors.allowed_headers,
            allow_credentials=settings.cors.allow_credentials,
            max_age=settings.cors.max_age,
            expose_headers=["X-Processing-Time-Ms"],
        )
