from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import EventType, Unit


class Bucket(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ProfitabilityRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: int
    asset_name: str
    currency: str
    income_total: Decimal
    expense_total: Decimal
    net: Decimal


class ProfitabilityReport(BaseModel):
    data: list[ProfitabilityRow]


class ProductionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bucket_start: datetime
    asset_id: int
    unit: Unit
    category_id: int | None
    total: Decimal


class ProductionReport(BaseModel):
    data: list[ProductionRow]
    bucket: Bucket
    type: EventType


class CostPerUnitRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: int
    asset_name: str
    currency: str
    quantity: Decimal
    expense_total: Decimal
    cost_per_unit: Decimal


class CostPerUnitReport(BaseModel):
    data: list[CostPerUnitRow]
    unit: Unit


class ProfitabilityQuery(FilterParams):
    asset_id: int | None = None


class ProductionQuery(FilterParams):
    asset_id: int | None = None
    type: EventType = EventType.PRODUCTION
    unit: Unit | None = None
    bucket: Bucket = Bucket.DAY


class CostPerUnitQuery(FilterParams):
    asset_id: int | None = None
    unit: Unit


class TimelineQuery(FilterParams):
    type: EventType | None = None
