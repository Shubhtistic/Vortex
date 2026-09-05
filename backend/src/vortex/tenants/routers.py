from fastapi import APIRouter

from vortex.shared.schemas import ApiResponseSchema
from src.vortex.shared.responses import ApiResponse
from src.vortex.shared.database import DbSessionDep
from src.vortex.auth.dependencies import CurrentUserDep, VerifiedAdminDep

from .exceptions import SlugAlreadyExistsErorr
from .services import ApiKeyService, TenantService
from .schemas import CreateApiKeyRequest, CreateTenantRequest

# --- router ---
router = APIRouter(tags=["Tenants"])


# ==== Tenants Routers =====


# --- create tenants ---
@router.post("/tenants", response_model=ApiResponseSchema)
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
@router.get("/tenants", response_model=ApiResponseSchema)
async def get_all_tenants(db_session: DbSessionDep, user_data: CurrentUserDep):

    tenants_dict = await TenantService.get_all_tenants(
        org_id=user_data.get("org_id"), db_session=db_session
    )

    return ApiResponse.success(
        message="successfully fetched tenants", data=tenants_dict
    )


# ====== Api Key Routers ======


@router.post("/tenants/api-key", response_model=ApiResponseSchema)
async def create_an_api_key(
    payload: CreateApiKeyRequest,
    db_session: DbSessionDep,
    user_data: VerifiedAdminDep,
):
    try:
        api_key_dict = await ApiKeyService.create_api_key(
            payload=payload,
            db_session=db_session,
            org_id=user_data.get("org_id"),
            user_id=user_data.get("user_id"),
        )
    except SlugAlreadyExistsErorr:
        return ApiResponse.error(message="this slug is already taken", code=409)

    return ApiResponse.success(
        data=api_key_dict,
        message="Api key created successfully. Please copy the api key and store it securely. It will not be shown again.",
    )


@router.get("/tenants/api-key", response_model=ApiResponseSchema)
async def get_all_api_keys(db_session: DbSessionDep, user_data: CurrentUserDep):

    api_keys_dict = await ApiKeyService.get_all_api_keys(
        tenant_id="pending", db_session=db_session
    )
    return ApiResponse.success(
        message="successfully fetched api keys", data=api_keys_dict
    )
