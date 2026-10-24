from pydantic import BaseModel, EmailStr, field_validator
from src.vortex.shared.utilities import reject_blank_text


class LoginRequest(BaseModel):
    org_slug: str
    email: EmailStr
    password: str

    _validate_text = field_validator("org_slug", "email", "password")(reject_blank_text)
