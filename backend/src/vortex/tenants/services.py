from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import SlugAlreadyExistsErorr
from .schemas import CreateTenantRequest, TenantRead
from .models import Tenant
from .repository import TenantRepository


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
