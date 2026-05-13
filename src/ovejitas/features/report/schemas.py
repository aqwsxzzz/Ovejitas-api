from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit


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


class ProfitabilityTotal(BaseModel):
    currency: str
    income_total: Decimal
    expense_total: Decimal
    net: Decimal


class ProfitabilityReport(BaseModel):
    data: list[ProfitabilityRow]
    totals: list[ProfitabilityTotal]


class AggregateMeasure(StrEnum):
    SUM_QUANTITY = "sum_quantity"
    SUM_AMOUNT = "sum_amount"
    COUNT = "count"


class AggregateRow(BaseModel):
    bucket: datetime
    group: str | None
    measure: AggregateMeasure
    value: Decimal


class AggregateMeta(BaseModel):
    type: EventType
    measure: AggregateMeasure
    bucket: Bucket
    group_key: str | None


class AggregateReport(BaseModel):
    data: list[AggregateRow]
    meta: AggregateMeta


class AggregateQuery(FilterParams):
    type: EventType
    bucket: Bucket = Bucket.DAY
    asset_id: int | None = None
    unit: Unit | None = None
    adjustment: InventoryAdjustment | None = None
    currency: str | None = None


class CostPerUnitRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: int
    asset_name: str
    currency: str
    quantity: Decimal
    expense_total: Decimal
    cost_per_unit: Decimal


class CostPerUnitTotal(BaseModel):
    currency: str
    quantity: Decimal
    expense_total: Decimal
    cost_per_unit: Decimal


class CostPerUnitReport(BaseModel):
    data: list[CostPerUnitRow]
    totals: list[CostPerUnitTotal]
    unit: Unit


class ProfitabilityQuery(FilterParams):
    asset_id: int | None = None


class CostPerUnitQuery(FilterParams):
    asset_id: int | None = None
    unit: Unit


class TimelineQuery(FilterParams):
    type: EventType | None = None


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
