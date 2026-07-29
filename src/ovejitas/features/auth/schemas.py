from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ovejitas.core.schemas import StrictModel
from ovejitas.features.farm.timezone import IanaTimezone


class RegisterInput(StrictModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    # The new farm's calendar. Every day boundary the API draws is anchored to
    # it, so a farm left on the UTC default reports a day that ends at 21:00
    # local in Montevideo. Optional to keep signup one step; changeable later
    # via PATCH /farms/{id}.
    timezone: IanaTimezone | None = None


class LoginInput(StrictModel):
    email: EmailStr
    password: str


class RefreshInput(StrictModel):
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
    default_currency: str


class MeResponse(BaseModel):
    user: UserRead
    memberships: list[FarmMembershipRead]
