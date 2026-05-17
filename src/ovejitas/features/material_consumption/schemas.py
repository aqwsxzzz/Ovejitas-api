from datetime import datetime
from decimal import Decimal
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.event.types import Unit
from ovejitas.features.material_consumption.guards import assert_consumer_rules
from ovejitas.features.material_consumption.types import ConsumptionReason


class MaterialConsumptionCreate(StrictModel):
    material_asset_id: int
    consumer_asset_id: int | None = None
    individual_id: int | None = None
    occurred_at: datetime
    quantity: Decimal = Field(gt=0)
    unit: Unit
    reason: ConsumptionReason
    notes: OptionalStr = None
    meta: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: OptionalStr = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def _consumer_rules(self) -> Self:
        assert_consumer_rules(self.reason, self.consumer_asset_id, self.individual_id)
        return self


class MaterialConsumptionUpdate(StrictModel):
    """PATCH body. ``material_asset_id`` is immutable — a different material is a
    different consumption record."""

    consumer_asset_id: int | None = None
    individual_id: int | None = None
    occurred_at: datetime | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    unit: Unit | None = None
    reason: ConsumptionReason | None = None
    notes: OptionalStr = None
    meta: dict[str, Any] | None = None


class MaterialConsumptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    material_asset_id: int
    consumer_asset_id: int | None
    individual_id: int | None
    inventory_event_id: int
    occurred_at: datetime
    quantity: Decimal
    unit: Unit
    reason: ConsumptionReason
    notes: str | None
    meta: dict[str, Any]
    idempotency_key: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime


class MaterialConsumptionFilters(FilterParams):
    material_asset_id: int | None = None
    consumer_asset_id: int | None = None
    reason: ConsumptionReason | None = None
