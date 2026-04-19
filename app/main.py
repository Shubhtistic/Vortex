from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.redis import close_redis_pool,init_redis_pool


# routers
from app.api.v1 import create
from app.api.v1 import analyse

# env variables
from app.core.config import settings


# this runs before app receives request
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs exactly once when the server starts
    print("starting redis loop..")
    await init_redis_pool()
    
    yield # api is now running and accepting requests
    
    # This runs exactly once when the server shuts down
    print("closing redis loop...")
    await close_redis_pool()


# give app the lifespan
app = FastAPI(title="Vortex Telemetry Engine", lifespan=lifespan,
              docs_url=f"/{settings.DOCS_ENDPOINT}",
              redoc_url=None)

# we set the docs_url to env variable 
# we can also disable it using docs_url = None


app.include_router(create.router, prefix="/api/v1")
app.include_router(analyse.router, prefix="/api/v1")

