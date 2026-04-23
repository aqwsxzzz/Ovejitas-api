from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str


class RefreshInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    created_at: datetime


class FarmMembershipRead(BaseModel):
    farm_id: int
    role: str


class MeResponse(BaseModel):
    user: UserRead
    memberships: list[FarmMembershipRead]
