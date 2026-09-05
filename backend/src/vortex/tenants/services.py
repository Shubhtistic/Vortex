from sqlalchemy.ext.asyncio import AsyncSession

from .utils import create_api_key, hash_api_key
from .exceptions import SlugAlreadyExistsErorr
from .schemas import ApiKeyRead, CreateApiKeyRequest, CreateTenantRequest, TenantRead
from .models import ApiKey, Tenant
from .repository import ApiKeyRepository, TenantRepository

# ====== Tenant Service ======


class TenantService:
    @staticmethod
    async def create_tenant(
        org_id: str,
        user_id: str,
        payload: CreateTenantRequest,
        db_session: AsyncSession,
    ) -> dict:

        # check if slug already exists
        if await TenantRepository.check_by_slug(
            slug=payload.slug, org_id=org_id, db_session=db_session
        ):
            raise SlugAlreadyExistsErorr

        payload_dict = payload.model_dump()

        payload_dict["organization_id"] = org_id
        payload_dict["created_by_user_id"] = user_id

        tenant_instance = Tenant(**payload_dict)

        # create the tenant in db
        await TenantRepository.create_tenant(
            tenant_instance=tenant_instance, db_session=db_session
        )

        # return dict data
        return TenantRead.model_validate(tenant_instance).model_dump()

    @staticmethod
    async def get_all_tenants(org_id: str, db_session: AsyncSession) -> list[dict]:

        tenants = await TenantRepository.get_all_tenants(
            org_id=org_id, db_session=db_session
        )

        if not tenants:
            return [{}]

        return [TenantRead.model_validate(tenant).model_dump() for tenant in tenants]


# ====== Api Key Service ======


class ApiKeyService:
    @staticmethod
    async def create_api_key(
        payload: CreateApiKeyRequest,
        db_session: AsyncSession,
        org_id: str,
        user_id: str,
    ) -> dict:
        # check if slug exists already
        if await ApiKeyRepository.check_by_api_key_slug(
            api_key_slug=payload.api_key_slug,
            tenant_id=payload.tenant_id,
            db_session=db_session,
        ):
            raise SlugAlreadyExistsErorr

        # new slug -> create new api key

        raw_api_key = create_api_key()
        api_key_raw_preview = raw_api_key[-4:]
        hashed_api_key = hash_api_key(raw_api_key)

        api_key_instance = ApiKey(
            organization_id=org_id,
            tenant_id=payload.tenant_id,
            api_key_slug=payload.api_key_slug,
            api_key_raw_preview=api_key_raw_preview,
            hashed_key=hashed_api_key,
            created_by_user_id=user_id,
        )

        api_key = await ApiKeyRepository.create_api_key(
            api_key_instance=api_key_instance, db_session=db_session
        )

        # return dict data
        return ApiKeyRead.model_validate(api_key).model_dump()

    @staticmethod
    async def get_all_api_keys(tenant_id: str, db_session: AsyncSession) -> list[dict]:

        query = await db_session.execute(
            """
            SELECT * FROM api_keys WHERE tenant_id = :tenant_id
            """,
            {"tenant_id": tenant_id},
        )

        api_keys = query.fetchall()

        if not api_keys:
            return [{}]

        return [ApiKeyRead.model_validate(api_key).model_dump() for api_key in api_keys]
