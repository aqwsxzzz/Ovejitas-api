from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ovejitas.core.filters import FilterParams
from ovejitas.features.asset.models import AssetKind, AssetMode


class AssetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    kind: AssetKind
    mode: AssetMode
    location: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1024)


class AssetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    kind: AssetKind | None = None
    mode: AssetMode | None = None
    location: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1024)


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    name: str
    kind: AssetKind
    mode: AssetMode
    location: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime


class AssetFilters(FilterParams):
    kind: AssetKind | None = None
    mode: AssetMode | None = None
