from fastapi import APIRouter

from src.vortex.organizations.routers import router as org_router
from src.vortex.auth.routers import router as auth_router
from src.vortex.tenants.routers import router as tenants_router

router = APIRouter()

router.include_router(org_router)
router.include_router(auth_router)
router.include_router(tenants_router)
