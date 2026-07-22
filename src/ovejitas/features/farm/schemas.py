from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ovejitas.core.schemas import StrictModel


class FarmRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    default_currency: str
    timezone: str
    created_at: datetime
    updated_at: datetime


class FarmUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    default_currency: str | None = Field(default=None, min_length=3, max_length=3)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("default_currency")
    @classmethod
    def _uppercase_iso(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.isalpha():
            raise ValueError("currency must be 3 letters (ISO 4217)")
        return v.upper()

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, v: str | None) -> str | None:
        # Allowlist by construction: only a name the tz database resolves is
        # accepted, so nothing arbitrary reaches astimezone at report time.
        if v is None:
            return v
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"unknown timezone {v!r} (expected an IANA name)") from exc
        return v
