from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.vortex.shared.database import create, check_exists, get_all

from .models import ApiKey, Tenant


class TenantRepository:
    @staticmethod
    async def create_tenant(
        tenant_instance: Tenant, db_session: AsyncSession
    ) -> Tenant:

        return await create(instance=tenant_instance, db_session=db_session)

    @staticmethod
    async def check_by_slug(slug: str, org_id: str, db_session: AsyncSession) -> bool:
        return await check_exists(
            model=Tenant,
            db_session=db_session,
            filters={"slug": slug, "organization_id": org_id},
        )

    @staticmethod
    async def get_all_tenants(
        org_id: str, db_session: AsyncSession
    ) -> Optional[list[Tenant]]:
        """get all tenants for this organisation"""

        query = select(Tenant).where(Tenant.organization_id == org_id)

        return await get_all(stmt=query, db_session=db_session)


class ApiKeyRepository:
    @staticmethod
    async def create_api_key(
        api_key_instance: ApiKey, db_session: AsyncSession
    ) -> ApiKey:

        return await create(instance=api_key_instance, db_session=db_session)

    @staticmethod
    async def check_by_api_key_slug(
        api_key_slug: str, tenant_id: str, db_session: AsyncSession
    ) -> bool:
        return await check_exists(
            model=ApiKey,
            db_session=db_session,
            filters={"api_key_slug": api_key_slug, "tenant_id": tenant_id},
        )
