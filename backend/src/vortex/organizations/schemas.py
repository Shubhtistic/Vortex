from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from .enums import InviteMembershipRole


class SignupRequest(BaseModel):
    org_name: str
    slug: str
    email: EmailStr
    password: str
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)


class InviteMemberRequest(BaseModel):
    password: str
    email: EmailStr
    role: InviteMembershipRole  # only "admin" or "analyst" accepted


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool
