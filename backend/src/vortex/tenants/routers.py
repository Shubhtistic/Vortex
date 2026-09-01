from fastapi import APIRouter

from src.vortex.shared.responses import ApiResponse
from src.vortex.shared.database import DbSessionDep
from src.vortex.auth.dependencies import CurrentUserDep, VerifiedAdminDep

from .exceptions import SlugAlreadyExistsErorr, NoTenantsFoundError
from .services import TenantService
from .schemas import CreateTenantRequest

# --- router ---
router = APIRouter()


# --- create tenants ---
@router.post("/tenants")
async def create_tenant(
    payload: CreateTenantRequest, db_session: DbSessionDep, user_data: VerifiedAdminDep
):

    # call service to save
    try:
        tenant_dict = await TenantService.create_tenant(
            org_id=user_data.get("org_id"),
            user_id=user_data.get("user_id"),
            payload=payload,
            db_session=db_session,
        )

    except SlugAlreadyExistsErorr:
        return ApiResponse.error(message="this slug is already taken", code=409)

    return ApiResponse.success(message="Tenant Created Successfully", data=tenant_dict)


# --- get all tenants ---
@router.get("/tenants")
async def get_all_tenants(db_session: DbSessionDep, user_data: CurrentUserDep):

    tenants_dict = await TenantService.get_all_tenants(
        org_id=user_data.get("org_id"), db_session=db_session
    )

    return ApiResponse.success(
        message="successfully fetched tenants", data=tenants_dict
    )
