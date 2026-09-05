from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from .enums import ApiKeyStatus, TenantStatus

# ====== tenant schemas ======


# --- create tenant schema ---
class CreateTenantRequest(BaseModel):

    tenant_name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(min_length=1, max_length=20)


# --- read tenant schema ---
class TenantRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_name: str
    slug: str
    created_at: datetime
    status: TenantStatus


# ======= Api key schemas =======


# --- create api key ----
class CreateApiKeyRequest(BaseModel):

    api_key_slug: str = Field(min_length=1, max_length=20)
    tenant_id: UUID | str


# --- read an api key ---
class ApiKeyRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    api_key_slug: str
    api_key_raw_preview: str
    status: ApiKeyStatus
