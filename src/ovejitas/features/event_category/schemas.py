from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import EventType


class EventCategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: EventType
    name: str = Field(min_length=1, max_length=128)
    color: str | None = Field(default=None, max_length=16)


class EventCategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    color: str | None = Field(default=None, max_length=16)
    archived_at: datetime | None = None


class EventCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    type: EventType
    name: str
    color: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EventCategoryFilters(FilterParams):
    type: EventType | None = None
    archived: bool | None = None
