from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.vortex.shared.config import get_settings

from .utils import create_api_key, hash_api_key, remove_api_key_from_cache
from .exceptions import ApiKeyAlreadyNonActiveError, SlugAlreadyExistsErorr
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
            logger.warning("Tenant creation rejected: slug already exists")
            raise SlugAlreadyExistsErorr

        payload_dict = payload.model_dump()

        payload_dict["organization_id"] = org_id
        payload_dict["created_by_user_id"] = user_id

        tenant_instance = Tenant(**payload_dict)

        # create the tenant in db
        await TenantRepository.create_tenant(
            tenant_instance=tenant_instance, db_session=db_session
        )
        logger.info("Tenant created")
        # return dict data
        return TenantRead.model_validate(tenant_instance).model_dump()

    @staticmethod
    async def get_all_tenants(
        org_id: str, db_session: AsyncSession, limit: int, page_num: int
    ) -> tuple[list[dict], int]:

        # calculate offset
        offset = (page_num - 1) * limit

        tenants, total_count = await TenantRepository.get_all_tenants(
            org_id=org_id, db_session=db_session, offset=offset, limit=limit
        )

        if not total_count:
            logger.debug("No tenants found")
            return [], 0

        return [
            TenantRead.model_validate(tenant).model_dump() for tenant in tenants
        ], total_count


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
            logger.warning("API key creation rejected: slug already exists")
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
        logger.info("API key created")
        # return dict data
        dict_data = ApiKeyRead.model_validate(api_key).model_dump()

        # add the raw key also for user to see
        dict_data["raw_api_key"] = raw_api_key

        return dict_data

    @staticmethod
    async def get_all_api_keys(
        tenant_id: str, db_session: AsyncSession, limit: int, page_num: int
    ) -> tuple[list[dict], int]:

        # calculate offset
        offset = (page_num - 1) * limit

        # call repo to get results

        api_keys, total_count = await ApiKeyRepository.get_all_api_keys(
            tenant_id=tenant_id, db_session=db_session, offset=offset, limit=limit
        )

        if total_count == 0:
            logger.debug("No API keys found")
            return [], 0

        return [
            ApiKeyRead.model_validate(api_key).model_dump() for api_key in api_keys
        ], total_count

    @staticmethod
    async def revoke_api_key(
        tenant_id: str, api_key_id: str, db_session: AsyncSession
    ) -> None:

        # check if this api is already revoked or not
        if await ApiKeyRepository.check_non_active_api_key_exists(
            api_key_id=api_key_id, tenant_id=tenant_id, db_session=db_session
        ):
            raise ApiKeyAlreadyNonActiveError

        # now mark in db as grace and add the grace time also
        GRACE_PERIOD_MINS = (get_settings()).project.grace_period_mins

        grace_period = datetime.now(timezone.utc) + timedelta(minutes=GRACE_PERIOD_MINS)

        # step 1 mark in db as grace period
        hashed_api_key = await ApiKeyRepository.mark_as_grace_and_get_hashed_key(
            api_key_id=api_key_id,
            tenant_id=tenant_id,
            grace_period=grace_period,
            db_session=db_session,
        )

        # now marked in db as grace
        # now remove the key from redis
        # afer removing all hits will go to where it will show grace period
        # and it will now set the ttl same as that of grace period
        # once grace period also hits key will be then set as revoked

        # step 2 -> remove from redis
        if hashed_api_key:
            try:
                await remove_api_key_from_cache(hashed_api_key)
            except Exception:
                # redis down then ->  DB is source of truth
                logger.exception("Could not remove revoked API key from cache")

        # done

        return None

    @staticmethod
    async def rotate_api_key(
        org_id: str,
        user_id: str,
        payload: ApiKeyRotateRequest,
        db_session: AsyncSession,
    ) -> dict:

        # step 1 -> check if this key is already revoked or in grace period
        if await ApiKeyRepository.check_non_active_api_key_exists(
            api_key_id=payload.api_key_id,
            tenant_id=payload.tenant_id,
            db_session=db_session,
        ):
            logger.warning("API key rotation rejected: key is already inactive")
            raise ApiKeyAlreadyNonActiveError

        # imp check if slug exists before marking as graced
        # if we grace the api first and then check slug
        # if slug fails the api key is already graced
        if await ApiKeyRepository.check_by_api_key_slug(
            api_key_slug=payload.api_key_slug,
            tenant_id=payload.tenant_id,
            db_session=db_session,
        ):
            logger.warning("API key rotation rejected: slug already exists")
            raise SlugAlreadyExistsErorr

        # step 2 -> exact revoke logic + create new api key logic

        # now mark in db as grace and add the grace time also
        GRACE_PERIOD_MINS = (get_settings()).project.grace_period_mins

        grace_period = datetime.now(timezone.utc) + timedelta(minutes=GRACE_PERIOD_MINS)

        # step 1 mark in db as grace period
        hashed_api_key = await ApiKeyRepository.mark_as_grace_and_get_hashed_key(
            api_key_id=payload.api_key_id,
            tenant_id=payload.tenant_id,
            grace_period=grace_period,
            db_session=db_session,
        )

        # step 2 -> remove from redis
        if hashed_api_key:
            try:
                await remove_api_key_from_cache(hashed_api_key)
            except Exception:
                # redis down, ignore - DB is source of truth
                logger.exception("Could not remove rotated API key from cache")

        # now that api is in grace period
        # create a new one and return new one to user

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
        logger.info("API key rotated")
        # return dict data
        dict_data = ApiKeyRead.model_validate(api_key).model_dump()

        # add the raw key also for user to see
        dict_data["raw_api_key"] = raw_api_key

        return dict_data
