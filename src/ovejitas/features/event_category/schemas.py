from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.event.types import EventType, Unit


class EventCategoryCreate(StrictModel):
    type: EventType
    name: str = Field(min_length=1, max_length=128)
    unit: Unit | None = None
    color: OptionalStr = Field(default=None, max_length=16)

    @model_validator(mode="after")
    def _unit_matches_type(self) -> Self:
        # A unit is the product's unit of measure — meaningful only for production
        # categories, and required there so every product is well-formed.
        if self.type is EventType.PRODUCTION and self.unit is None:
            raise ValueError("Production categories require a unit")
        if self.type is not EventType.PRODUCTION and self.unit is not None:
            raise ValueError("Only production categories may have a unit")
        return self


class EventCategoryUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    unit: Unit | None = None
    color: OptionalStr = Field(default=None, max_length=16)
    archived_at: datetime | None = None


class EventCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    type: EventType
    name: str
    unit: Unit | None
    # The pool this product harvests into — provisioned by the API, not the client.
    produce_asset_id: int | None
    color: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EventCategoryFilters(FilterParams):
    type: EventType | None = None
    archived: bool | None = None
