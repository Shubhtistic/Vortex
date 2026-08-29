from fastapi import APIRouter

from src.vortex.organizations.routers import router as org_router

router = APIRouter()

router.include_router(org_router)
