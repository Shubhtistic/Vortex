from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.vortex.shared.utilities import reject_blank_text

from .enums import ApiKeyStatus, TenantStatus

# ====== tenant schemas ======


# --- create tenant schema ---
class CreateTenantRequest(BaseModel):

    tenant_name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(min_length=1, max_length=20)

    _validate_text = field_validator("tenant_name", "slug")(reject_blank_text)


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

    _validate_text = field_validator("api_key_slug", "tenant_id")(reject_blank_text)


# --- read an api key ---
class ApiKeyRead(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    api_key_slug: str
    api_key_raw_preview: str
    status: ApiKeyStatus


# --- rotate a api key ---
class ApiKeyRotateRequest(BaseModel):
    api_key_id: str
    tenant_id: str
    api_key_slug: str = Field(min_length=1, max_length=20)

    _validate_text = field_validator("api_key_id", "tenant_id", "api_key_slug")(
        reject_blank_text
    )
