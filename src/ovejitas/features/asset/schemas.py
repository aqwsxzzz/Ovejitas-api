from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.asset.models import AssetKind, AssetMode

# Sanity bounds, not biology: wide enough for every farmed species, narrow
# enough to catch a farmer typing weeks or months into a days field.
GestationDays = Annotated[int | None, Field(default=None, ge=20, le=400)]


class AssetCreate(StrictModel):
    name: str = Field(min_length=1, max_length=255)
    kind: AssetKind
    mode: AssetMode | None = None
    location: OptionalStr = Field(default=None, max_length=255)
    description: OptionalStr = Field(default=None, max_length=1024)
    gestation_days: GestationDays = None


class AssetUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    kind: AssetKind | None = None
    mode: AssetMode | None = None
    location: OptionalStr = Field(default=None, max_length=255)
    description: OptionalStr = Field(default=None, max_length=1024)
    produce_asset_id: int | None = None
    gestation_days: GestationDays = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    name: str
    kind: AssetKind
    mode: AssetMode | None
    location: str | None
    description: str | None
    produce_asset_id: int | None
    gestation_days: int | None
    created_at: datetime
    updated_at: datetime


class AssetFilters(FilterParams):
    kind: AssetKind | None = None
    mode: AssetMode | None = None


class AssetKindCount(BaseModel):
    kind: AssetKind
    count: int


class AssetSummary(BaseModel):
    data: list[AssetKindCount]
