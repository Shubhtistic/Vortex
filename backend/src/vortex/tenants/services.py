from datetime import datetime, timedelta, timezone
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.vortex.infrastructure.config import get_settings
from src.vortex.infrastructure.database import get_db_session

from .utils import create_api_key, hash_api_key, remove_api_key_from_cache
from .exceptions import (
    ApiKeyAlreadyNonActiveError,
    SlugAlreadyExistsErorr,
    TenantNotFoundError,
)

from .schemas import (
    ApiKeyRead,
    ApiKeyRotateRequest,
    CreateApiKeyRequest,
    CreateTenantRequest,
    TenantRead,
)
from .models import ApiKey, Tenant
from .repository import ApiKeyRepository, TenantRepository

logger = logging.getLogger(__name__)

# ====== Tenant Service ======


class TenantService:
    @staticmethod
    async def ensure_tenant_in_org(
        tenant_id: UUID, org_id: UUID, db_session: AsyncSession
    ) -> None:
        """Reject tenant-scoped operations unless the tenant belongs to the caller."""

        tenant_exists = await TenantRepository.exists_by_id_and_org(
            tenant_id=tenant_id, org_id=org_id, db_session=db_session
        )
        if not tenant_exists:
            logger.warning(
                "Tenant access rejected: tenant not found in caller organization"
            )
            raise TenantNotFoundError

    @staticmethod
    async def create_tenant(
        org_id: UUID,
        user_id: UUID,
        payload: CreateTenantRequest,
    ) -> dict:
        async with get_db_session() as db_session:
            if await TenantRepository.check_by_slug(
                slug=payload.slug, org_id=org_id, db_session=db_session
            ):
                logger.warning("Tenant creation rejected: slug already exists")
                raise SlugAlreadyExistsErorr

            payload_dict = payload.model_dump()
            payload_dict["organization_id"] = org_id
            payload_dict["created_by_user_id"] = user_id
            tenant_instance = Tenant(**payload_dict)

            await TenantRepository.create_tenant(
                tenant_instance=tenant_instance, db_session=db_session
            )
            logger.info("Tenant created")
            return TenantRead.model_validate(tenant_instance).model_dump()

    @staticmethod
    async def get_all_tenants(
        org_id: UUID, limit: int, page_num: int
    ) -> tuple[list[dict], int]:
        async with get_db_session() as db_session:
            offset = (page_num - 1) * limit

            tenants, total_count = await TenantRepository.get_all_tenants(
                org_id=org_id, db_session=db_session, offset=offset, limit=limit
            )

            if not total_count:
                logger.debug("No tenants found")
                return [], 0

            return [
                TenantRead.model_validate(tenant).model_dump()
                for tenant in tenants
            ], total_count


# ====== Api Key Service ======


class ApiKeyService:
    @staticmethod
    async def create_api_key(
        payload: CreateApiKeyRequest,
        org_id: UUID,
        user_id: UUID,
    ) -> dict:
        async with get_db_session() as db_session:
            await TenantService.ensure_tenant_in_org(
                tenant_id=payload.tenant_id, org_id=org_id, db_session=db_session
            )
            if await ApiKeyRepository.check_by_api_key_slug(
                api_key_slug=payload.api_key_slug,
                tenant_id=payload.tenant_id,
                org_id=org_id,
                db_session=db_session,
            ):
                logger.warning("API key creation rejected: slug already exists")
                raise SlugAlreadyExistsErorr

            raw_api_key = create_api_key()
            api_key_instance = ApiKey(
                organization_id=org_id,
                tenant_id=payload.tenant_id,
                api_key_slug=payload.api_key_slug,
                api_key_raw_preview=raw_api_key[-4:],
                hashed_key=hash_api_key(raw_api_key),
                created_by_user_id=user_id,
            )
            api_key = await ApiKeyRepository.create_api_key(
                api_key_instance=api_key_instance, db_session=db_session
            )
            logger.info("API key created")
            dict_data = ApiKeyRead.model_validate(api_key).model_dump()
            dict_data["raw_api_key"] = raw_api_key
            return dict_data

    @staticmethod
    async def get_all_api_keys(
        org_id: UUID,
        tenant_id: UUID,
        limit: int,
        page_num: int,
    ) -> tuple[list[dict], int]:
        async with get_db_session() as db_session:
            offset = (page_num - 1) * limit
            api_keys, total_count = await ApiKeyRepository.get_all_api_keys(
                tenant_id=tenant_id,
                org_id=org_id,
                db_session=db_session,
                offset=offset,
                limit=limit,
            )
            if total_count == 0:
                logger.debug("No API keys found")
                return [], 0
            return [
                ApiKeyRead.model_validate(api_key).model_dump()
                for api_key in api_keys
            ], total_count

    @staticmethod
    async def revoke_api_key(
        org_id: UUID, tenant_id: UUID, api_key_id: UUID
    ) -> None:
        async with get_db_session() as db_session:
            grace_period_minutes = get_settings().project.grace_period_mins
            grace_period = datetime.now(timezone.utc) + timedelta(
                minutes=grace_period_minutes
            )
            hashed_api_key = await ApiKeyRepository.mark_as_grace_and_get_hashed_key(
                api_key_id=api_key_id,
                tenant_id=tenant_id,
                org_id=org_id,
                grace_period=grace_period,
                db_session=db_session,
            )
            if hashed_api_key is None:
                is_non_active = await ApiKeyRepository.check_non_active_api_key_exists(
                    api_key_id=api_key_id,
                    tenant_id=tenant_id,
                    org_id=org_id,
                    db_session=db_session,
                )
                if is_non_active:
                    raise ApiKeyAlreadyNonActiveError

            if hashed_api_key:
                try:
                    await remove_api_key_from_cache(hashed_api_key)
                except Exception:
                    logger.exception("Could not remove revoked API key from cache")

    @staticmethod
    async def rotate_api_key(
        org_id: UUID,
        user_id: UUID,
        payload: ApiKeyRotateRequest,
    ) -> dict:
        async with get_db_session() as db_session:
            await TenantService.ensure_tenant_in_org(
                tenant_id=payload.tenant_id, org_id=org_id, db_session=db_session
            )
            is_non_active, slug_exists = await ApiKeyRepository.get_rotation_conflicts(
                api_key_id=payload.api_key_id,
                tenant_id=payload.tenant_id,
                org_id=org_id,
                api_key_slug=payload.api_key_slug,
                db_session=db_session,
            )
            if is_non_active:
                logger.warning("API key rotation rejected: key is already inactive")
                raise ApiKeyAlreadyNonActiveError

            if slug_exists:
                logger.warning("API key rotation rejected: slug already exists")
                raise SlugAlreadyExistsErorr

            GRACE_PERIOD_MINS = (get_settings()).project.grace_period_mins
            grace_period = datetime.now(timezone.utc) + timedelta(
                minutes=GRACE_PERIOD_MINS
            )
            hashed_api_key = await ApiKeyRepository.mark_as_grace_and_get_hashed_key(
                api_key_id=payload.api_key_id,
                tenant_id=payload.tenant_id,
                org_id=org_id,
                grace_period=grace_period,
                db_session=db_session,
            )

            if hashed_api_key:
                try:
                    await remove_api_key_from_cache(hashed_api_key)
                except Exception:
                    # redis down, ignore - DB is source of truth
                    logger.exception("Could not remove rotated API key from cache")

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
            logger.info("API key rotated")
            dict_data = ApiKeyRead.model_validate(api_key).model_dump()
            dict_data["raw_api_key"] = raw_api_key
            return dict_data
