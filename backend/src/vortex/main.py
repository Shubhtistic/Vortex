from contextlib import asynccontextmanager
import logging
from fastapi.exceptions import RequestValidationError
from scalar_fastapi import get_scalar_api_reference
from fastapi import FastAPI, HTTPException, Request

from src.vortex.shared.middleware import CORSMiddlewareWithSettings, log_requests
from src.vortex.shared.redpanda_client import RedpandaProducer
from src.vortex.shared.responses import ApiResponse
from src.vortex.shared.redis_client import init_redis, close_redis
from src.vortex.api.routers import router as api_router
from src.vortex.shared.logging_config import setup_logging
from src.vortex.shared.config import get_settings

logger = logging.getLogger(__name__)

# -- setup the loggger ---
setup_logging()


# --- lifespan handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_redis()
        logger.info("Application startup completed")
        await RedpandaProducer.start()

        yield
    except Exception:
        logger.exception("Application lifecycle failed")
        raise
    finally:
        await RedpandaProducer.stop()
        await close_redis()
        logger.info("Application shutdown completed")


# --- create app ---
app = FastAPI(lifespan=lifespan)


# --- exception handler ---


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP exception",
        extra={"status_code": exc.status_code, "path": request.url.path},
    )
    return ApiResponse.error(message=exc.detail, code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    logger.warning("Request validation failed", extra={"path": request.url.path})
    return ApiResponse.error(
        message="Validation failed",
        code=422,
        data=None,
        meta={
            "path": str(request.url),
            "errors": exc.errors(),
        },
    )


# ===== Add Middlewares ====

# --- Cors Middleware Policy ---
app.add_middleware(CORSMiddlewareWithSettings)

# --- logging midleware ---
if get_settings().app.environment.lower() != "live":

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        return await log_requests(request, call_next)


# --- imports routers ---
app.include_router(api_router)


# --- scalar docs ---
@app.get("/", include_in_schema=False)
async def scalar():
    return get_scalar_api_reference(openapi_url=app.openapi_url)
