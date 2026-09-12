from fastapi import APIRouter, Query

from src.vortex.shared.responses import ApiResponse
from src.vortex.shared.database import DbSessionDep
from src.vortex.auth.dependencies import CurrentUserDep, VerifiedAdminDep

from .exceptions import ApiKeyAlreadyNonActiveError, SlugAlreadyExistsErorr
from .services import ApiKeyService, TenantService
from .schemas import ApiKeyRotateRequest, CreateApiKeyRequest, CreateTenantRequest

# --- router ---
router = APIRouter(tags=["Tenants"])


# ==== Tenants Routers =====


# --- create tenants ---
@router.post("/tenants")
async def create_tenant(
    payload: CreateTenantRequest,
    db_session: DbSessionDep,
    user_data: VerifiedAdminDep,
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
async def get_all_tenants(
    db_session: DbSessionDep,
    user_data: CurrentUserDep,
    limit: int = Query(10, ge=1, le=50, description="items per page"),
    page_num: int = Query(1, ge=1, description="current page num"),
):

    # get tenants data with thier count
    tenants_dict, total_count = await TenantService.get_all_tenants(
        org_id=user_data.get("org_id"),
        db_session=db_session,
        limit=limit,
        page_num=page_num,
    )
    # total pages
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

    return ApiResponse.success(
        message="successfully fetched tenants",
        data=tenants_dict,
        meta={
            "limit": limit,
            "page_num": page_num,
            "total_count": total_count,
            "total_pages": total_pages,
        },
    )


# ====== Api Key Routers ======


@router.post("/tenants/api-key")
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


@router.get("/tenants/api-keys")
async def get_all_api_keys(
    tenant_id: str,
    db_session: DbSessionDep,
    user_data: CurrentUserDep,
    limit: int = Query(10, ge=1, le=50, description="items per page"),
    page_num: int = Query(1, ge=1, description="current page num"),
):

    api_keys_dict, total_count = await ApiKeyService.get_all_api_keys(
        tenant_id=tenant_id,
        db_session=db_session,
        limit=limit,
        page_num=page_num,
    )
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

    return ApiResponse.success(
        message="successfully fetched api keys",
        data=api_keys_dict,
        meta={
            "page_num": page_num,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
        },
    )


@router.delete("/tenants/{tenant_id}/api-keys/{api_key_id}", status_code=204)
async def revoke_api_key(
    tenant_id: str,
    api_key_id: str,
    db_session: DbSessionDep,
    user_data: VerifiedAdminDep,
):
    # call service to delete the api_key_id
    try:
        await ApiKeyService.revoke_api_key(
            tenant_id=tenant_id, api_key_id=api_key_id, db_session=db_session
        )
    except ApiKeyAlreadyNonActiveError:
        return ApiResponse.error(
            message="This Key is already revoked or it may already be in grace period",
            code=409,
        )


@router.post("/tenants/api-keys/rotate")
async def rotate_api_key(
    payload: ApiKeyRotateRequest,
    db_session: DbSessionDep,
    user_data: VerifiedAdminDep,
):
    try:
        result_dict = await ApiKeyService.rotate_api_key(
            org_id=user_data.get("org_id"),
            user_id=user_data.get("user_id"),
            payload=payload,
            db_session=db_session,
        )
    except ApiKeyAlreadyNonActiveError:
        return ApiResponse.error(
            code=409, message="The key is already revoked or is in grace period"
        )

    except SlugAlreadyExistsErorr:
        return ApiResponse.error(code=409, message="The key slug is already taken")

    return ApiResponse.success(
        data=result_dict,
        message="Api key created successfully. Please copy the api key and store it securely. It will not be shown again.",
    )
