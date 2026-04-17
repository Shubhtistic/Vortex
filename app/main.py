from fastapi import FastAPI
from contextlib import asynccontextmanager


# routers
from app.api.v1 import create
from app.api.v1 import analyse

# env variables
from app.core.config import settings


# this runs before app receives request
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


# give app the lifespan
app = FastAPI(title="Vortex Telemetry Engine", lifespan=lifespan,
              docs_url=settings.DOCS_ENDPOINT,
              redoc_url=None)

# we set the docs_url to env variable 
# you can also disable it using docs_url = None


app.include_router(create.router, prefix="/api/v1")
app.include_router(analyse.router, prefix="/api/v1")

