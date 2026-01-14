from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from contextlib import asynccontextmanager
from app.api.v1 import create
from app.db.session import init_db


# this runs before app receives request
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating db tables..")
    init_db()
    print("db tables created")
    yield


# giev app the lifespan
app = FastAPI(title="Vortex Telemetry Engine", lifespan=lifespan)


app.include_router(create.router, prefix="/api/v1")


@app.get("/")
def health():
    # FastAPI automatically converts this Dictionary to JSON.
    return {"status": "active", "system": "Vortex API"}


@app.get("/scalar/", include_in_schema=False)
def scalar_endpoint():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title="Vortex Api")
