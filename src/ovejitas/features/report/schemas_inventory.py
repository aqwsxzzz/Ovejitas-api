"""Schemas for the inventory-summary report — current on-hand stock per
(asset, unit)."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import Unit


class InventorySummaryRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: int
    asset_name: str
    unit: Unit
    on_hand: Decimal


class InventorySummaryReport(BaseModel):
    data: list[InventorySummaryRow]


class InventorySummaryQuery(FilterParams):
    asset_id: int | None = None
