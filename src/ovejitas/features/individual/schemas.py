from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.individual.models import IndividualStatus


class IndividualCreate(StrictModel):
    tag: str = Field(min_length=1, max_length=128)
    name: OptionalStr = Field(default=None, max_length=255)
    birth_date: date | None = None
    mother_id: int | None = None
    father_id: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class IndividualUpdate(StrictModel):
    name: OptionalStr = Field(default=None, max_length=255)
    tag: str | None = Field(default=None, min_length=1, max_length=128)
    birth_date: date | None = None
    mother_id: int | None = None
    father_id: int | None = None
    status: IndividualStatus | None = None
    extra: dict[str, Any] | None = None


class IndividualRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    asset_id: int
    name: str | None
    tag: str
    birth_date: date | None
    mother_id: int | None
    father_id: int | None
    status: IndividualStatus
    extra: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class IndividualFilters(FilterParams):
    status: IndividualStatus | None = None
