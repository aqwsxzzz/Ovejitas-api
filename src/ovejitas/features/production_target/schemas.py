from datetime import date, datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import StrictModel
from ovejitas.features.production_target.types import ProductionBasis, TargetPeriod


class AssetProductionTargetCreate(StrictModel):
    asset_id: int
    category_id: int
    basis: ProductionBasis
    expected_rate: Decimal = Field(ge=0)
    period: TargetPeriod | None = None
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def _check_basis_and_dates(self) -> Self:
        continuous = self.basis is ProductionBasis.PER_HEAD_CONTINUOUS
        if continuous and self.period is None:
            raise ValueError("per_head_continuous targets require a period")
        if not continuous and self.period is not None:
            raise ValueError("period is only valid for per_head_continuous targets")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must be on or after effective_from")
        return self


class AssetProductionTargetUpdate(StrictModel):
    # Identity/semantics (asset, category, basis, period, effective_from) are
    # immutable — a changed rate is a new effective-dated row. Only these adjust.
    expected_rate: Decimal | None = Field(default=None, ge=0)
    effective_to: date | None = None
    archived_at: datetime | None = None


class AssetProductionTargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    asset_id: int
    category_id: int
    basis: ProductionBasis
    expected_rate: Decimal
    period: TargetPeriod | None
    effective_from: date
    effective_to: date | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AssetProductionTargetFilters(FilterParams):
    asset_id: int | None = None
    category_id: int | None = None
    basis: ProductionBasis | None = None
    archived: bool | None = None
