from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    org_slug: str
    email: EmailStr
    password: str
