from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.event.types import Unit


class MaterialPurchaseCreate(StrictModel):
    material_asset_id: int
    occurred_at: datetime
    quantity: Decimal = Field(gt=0)
    unit: Unit
    amount: Decimal = Field(gt=0)
    supplier: OptionalStr = Field(default=None, max_length=255)
    notes: OptionalStr = None
    meta: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: OptionalStr = Field(default=None, max_length=128)


class MaterialPurchaseUpdate(StrictModel):
    """PATCH body. ``material_asset_id`` is immutable — a different material is a
    different purchase."""

    occurred_at: datetime | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    unit: Unit | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    supplier: OptionalStr = Field(default=None, max_length=255)
    notes: OptionalStr = None
    meta: dict[str, Any] | None = None


class MaterialPurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    material_asset_id: int
    inventory_event_id: int
    expense_event_id: int
    occurred_at: datetime
    quantity: Decimal
    unit: Unit
    amount: Decimal
    currency: str
    supplier: str | None
    notes: str | None
    meta: dict[str, Any]
    idempotency_key: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime


class MaterialPurchaseFilters(FilterParams):
    material_asset_id: int | None = None
