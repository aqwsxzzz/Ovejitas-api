from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import StrictModel
from ovejitas.features.farm_member.models import FarmRole


class MemberUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role: FarmRole
    created_at: datetime
    user: MemberUserRead


class MemberFilters(FilterParams):
    role: FarmRole | None = None


class MemberRoleUpdate(StrictModel):
    role: FarmRole
