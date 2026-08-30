from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from scalar_fastapi import get_scalar_api_reference
from fastapi import FastAPI, HTTPException, Request

from src.vortex.shared.responses import ApiResponse
from src.vortex.shared.redis_client import init_redis, close_redis
from src.vortex.api.routers import router as api_router


# --- lifespan handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()

    yield

    await close_redis()


# --- create app ---
app = FastAPI(lifespan=lifespan)


# --- exception handler ---


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return ApiResponse.error(message=exc.detail, code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return ApiResponse.error(
        message="Validation failed",
        code=422,
        data=None,
        meta={
            "path": str(request.url),
            "errors": exc.errors(),
        },
    )


# --- imports routers ---

app.include_router(api_router)


# --- scalar docs ---
@app.get("/", include_in_schema=False)
async def scalar():
    return get_scalar_api_reference(openapi_url=app.openapi_url)
