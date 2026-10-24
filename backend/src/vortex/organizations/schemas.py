from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from src.vortex.shared.utilities import reject_blank_text

from .enums import InviteMembershipRole, MembershipRole


class SignupRequest(BaseModel):
    org_name: str
    slug: str
    email: EmailStr
    password: str
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)

    _validate_text = field_validator(
        "org_name", "slug", "email", "password", "first_name", "last_name"
    )(reject_blank_text)


class InviteMemberRequest(BaseModel):
    first_name: str
    last_name: str
    password: str
    email: EmailStr
    role: InviteMembershipRole  # only "admin" or "analyst" accepted

    _validate_text = field_validator("first_name", "last_name", "password", "email")(
        reject_blank_text
    )


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    organization_id: UUID
    role: MembershipRole
    created_at: datetime


class OrgMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    role: MembershipRole
    email: EmailStr
    first_name: str
    last_name: str


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime
