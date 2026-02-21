from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from contextlib import asynccontextmanager
from app.db.session import engine


# routers
from app.api.v1 import create
from app.api.v1 import analyse


# this runs before app receives request
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


# giev app the lifespan
app = FastAPI(title="Vortex Telemetry Engine", lifespan=lifespan)


app.include_router(create.router, prefix="/api/v1")
app.include_router(analyse.router, prefix="/api/v1")


@app.get("/")
def health():
    # fastapi will convert this dict into json automatically
    return {"status": "active", "system": "Vortex API"}


@app.get("/scalar/", include_in_schema=False)
def scalar_endpoint():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title="Vortex Api")
