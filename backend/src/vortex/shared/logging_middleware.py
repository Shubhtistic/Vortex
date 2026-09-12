# middleware/logging_middleware.py
import time
import uuid
import logging
from contextvars import ContextVar
from starlette.types import ASGIApp, Receive, Scope, Send

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
logger = logging.getLogger("app.request")


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # only handle actual HTTP requests, pass through anything else (lifespan, websocket) untouched
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        request_id_ctx.set(request_id)
        start = time.perf_counter()
        status_code = {"code": None}

        async def send_wrapper(message):
            # intercept the outgoing response just to capture the status code
            # and inject our request-id header, then pass it through untouched otherwise
            if message["type"] == "http.response.start":
                status_code["code"] = message["status"]
                headers = message.setdefault("headers", [])
                headers.append((b"x-request-id", request_id.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            logger.exception(
                "request failed",
                extra={
                    "request_id": request_id,
                    "method": scope["method"],
                    "path": scope["path"],
                },
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method": scope["method"],
                "path": scope["path"],
                "status_code": status_code["code"],
                "duration_ms": round(duration_ms, 2),
            },
        )


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True
