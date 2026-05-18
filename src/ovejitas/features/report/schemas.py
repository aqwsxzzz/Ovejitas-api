from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit
from ovejitas.features.material_consumption.types import ConsumptionReason


class Bucket(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class GroupBy(StrEnum):
    ASSET = "asset"


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
    group_label: str | None = None
    measure: AggregateMeasure
    value: Decimal
    asset_id: int | None = None
    unit: Unit | None = None


class AggregateMeta(BaseModel):
    type: EventType
    measure: AggregateMeasure
    bucket: Bucket
    group_key: str | None
    group_by: GroupBy | None = None


class AggregateReport(BaseModel):
    data: list[AggregateRow]
    meta: AggregateMeta


class AggregateQuery(FilterParams):
    type: EventType
    bucket: Bucket = Bucket.DAY
    group_by: GroupBy | None = None
    asset_id: int | None = None
    unit: Unit | None = None
    adjustment: InventoryAdjustment | None = None
    currency: str | None = None


class CostPerUnitRow(BaseModel):
    asset_id: int
    asset_name: str
    currency: str
    production_quantity: Decimal
    direct_expense_total: Decimal
    consumed_material_cost: Decimal
    total_cost: Decimal
    # null when the producer made nothing in the window (no divide-by-zero)
    cost_per_unit: Decimal | None
    # true when feed it consumed has no purchase history to value it — the
    # cost is then understated and the row says so rather than hide it
    has_unvalued_consumption: bool


class CostPerUnitReport(BaseModel):
    data: list[CostPerUnitRow]
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


class ConsumptionGroupBy(StrEnum):
    MATERIAL = "material"
    CONSUMER = "consumer"
    BOTH = "both"


class MaterialConsumptionAggregateQuery(FilterParams):
    bucket: Bucket = Bucket.DAY
    group_by: ConsumptionGroupBy = ConsumptionGroupBy.MATERIAL
    material_asset_id: int | None = None
    consumer_asset_id: int | None = None
    reason: ConsumptionReason | None = None


class MaterialConsumptionAggregateTotal(BaseModel):
    group: str | None
    group_label: str | None
    unit: Unit
    total_qty: Decimal


class MaterialConsumptionAggregateReport(BaseModel):
    data: list[AggregateRow]
    totals: list[MaterialConsumptionAggregateTotal]
    bucket: Bucket
    group_by: ConsumptionGroupBy
