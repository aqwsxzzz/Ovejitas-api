from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ovejitas.core.schemas import StrictModel


class FarmRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    default_currency: str
    created_at: datetime
    updated_at: datetime


class FarmUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    default_currency: str | None = Field(default=None, min_length=3, max_length=3)

    @field_validator("default_currency")
    @classmethod
    def _uppercase_iso(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.isalpha():
            raise ValueError("currency must be 3 letters (ISO 4217)")
        return v.upper()
