from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from .enums import TenantStatus


# --- create tenant schema ---
class CreateTenantRequest(BaseModel):
    tenant_name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(min_length=1, max_length=20)


class TenantRead(BaseModel):
    id: UUID
    tenant_name: str
    slug: str
    created_at: datetime
    status: TenantStatus
