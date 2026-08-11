from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.asset.models import Asset, AssetKind, AssetMode

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
    # Set to take the asset out of circulation, null to bring it back. Always
    # permitted, however much history the asset carries — archiving destroys
    # nothing, which is the whole point of having it.
    archived_at: datetime | None = None


class AssetFields(BaseModel):
    """The asset's own columns, read straight off the model."""

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
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AssetRead(AssetFields):
    """An asset as the API returns it: its columns plus whether DELETE can succeed.

    ``deletable`` has no default and no model attribute behind it — it must be
    passed through ``of()``, so a caller cannot accidentally serialize an asset
    with an optimistic guess about an outcome it never checked.
    """

    deletable: bool

    @classmethod
    def of(cls, asset: Asset, *, deletable: bool) -> Self:
        return cls(**AssetFields.model_validate(asset).model_dump(), deletable=deletable)


class AssetFilters(FilterParams):
    kind: AssetKind | None = None
    mode: AssetMode | None = None
    # Retired assets are absent unless asked for, so every existing list call
    # quietly stops offering them without having to opt in.
    archived: bool = False


class AssetKindCount(BaseModel):
    kind: AssetKind
    count: int


class AssetSummary(BaseModel):
    data: list[AssetKindCount]
