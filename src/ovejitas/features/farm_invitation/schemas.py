from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import StrictModel
from ovejitas.features.farm_invitation.models import InvitationStatus
from ovejitas.features.farm_member.models import FarmRole


class InvitationCreate(StrictModel):
    email: EmailStr
    role: FarmRole

    @field_validator("role")
    @classmethod
    def _reject_owner(cls, value: FarmRole) -> FarmRole:
        if value is FarmRole.OWNER:
            raise ValueError("Cannot invite a member as owner")
        return value


class AcceptInvitation(StrictModel):
    # Always required: verifies an existing account, or sets the new account's password.
    password: str = Field(min_length=8, max_length=128)
    # Required only when the email has no account yet (enforced server-side).
    name: str | None = Field(default=None, min_length=1, max_length=255)


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    email: EmailStr
    role: FarmRole
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime


class InvitationCreateResponse(BaseModel):
    invitation: InvitationRead
    # Opaque token, returned exactly once at creation; only its hash is stored.
    token: str


class InvitationResolve(BaseModel):
    farm_id: int
    farm_name: str
    role: FarmRole
    email: EmailStr
    requires_registration: bool


class InvitationFilters(FilterParams):
    status: InvitationStatus | None = None
