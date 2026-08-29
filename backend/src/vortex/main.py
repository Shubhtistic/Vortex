from contextlib import asynccontextmanager
from scalar_fastapi import get_scalar_api_reference
from fastapi import FastAPI, HTTPException

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
async def http_exception_handler(request, exc: HTTPException):
    return ApiResponse.error(message=exc.detail, code=exc.status_code)


# --- imports routers ---

app.include_router(api_router)




# --- scalar docs ---
@app.get("/", include_in_schema=False)
async def scalar():
    return get_scalar_api_reference(openapi_url=app.openapi_url)
