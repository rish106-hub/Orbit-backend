from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import MeResponse


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1)
    default_timezone: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class AuthResponse(BaseModel):
    token: str
    user: MeResponse
