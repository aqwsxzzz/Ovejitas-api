from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.currency.types import normalize_code

Code = Annotated[str, Field(min_length=3, max_length=3)]


class CurrencyCreate(StrictModel):
    code: Code
    name: str = Field(min_length=1, max_length=64)
    symbol: OptionalStr = Field(default=None, max_length=8)

    @field_validator("code")
    @classmethod
    def _supported_iso(cls, v: str) -> str:
        try:
            return normalize_code(v)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc


class CurrencyUpdate(StrictModel):
    # `code` is intentionally absent: it is frozen after creation.
    name: str | None = Field(default=None, min_length=1, max_length=64)
    symbol: OptionalStr = Field(default=None, max_length=8)
    archived_at: datetime | None = None


class CurrencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    code: str
    name: str
    symbol: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CurrencyFilters(FilterParams):
    archived: bool | None = None
