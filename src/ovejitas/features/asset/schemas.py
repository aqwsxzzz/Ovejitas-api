from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.asset.models import AssetKind, AssetMode


class AssetCreate(StrictModel):
    name: str = Field(min_length=1, max_length=255)
    kind: AssetKind
    mode: AssetMode
    location: OptionalStr = Field(default=None, max_length=255)
    description: OptionalStr = Field(default=None, max_length=1024)
    expected_eggs_per_head_per_day: Decimal | None = Field(default=None, ge=0)


class AssetUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    kind: AssetKind | None = None
    mode: AssetMode | None = None
    location: OptionalStr = Field(default=None, max_length=255)
    description: OptionalStr = Field(default=None, max_length=1024)
    produce_asset_id: int | None = None
    expected_eggs_per_head_per_day: Decimal | None = Field(default=None, ge=0)


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    name: str
    kind: AssetKind
    mode: AssetMode
    location: str | None
    description: str | None
    produce_asset_id: int | None
    expected_eggs_per_head_per_day: Decimal | None
    created_at: datetime
    updated_at: datetime


class AssetFilters(FilterParams):
    kind: AssetKind | None = None
    mode: AssetMode | None = None
