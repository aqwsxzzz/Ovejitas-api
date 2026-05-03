from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.event.types import EventType


class EventCategoryCreate(StrictModel):
    type: EventType
    name: str = Field(min_length=1, max_length=128)
    color: OptionalStr = Field(default=None, max_length=16)


class EventCategoryUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    color: OptionalStr = Field(default=None, max_length=16)
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
