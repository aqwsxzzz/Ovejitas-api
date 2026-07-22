"""Schemas for the time-bucketed aggregate reports — the generic event
aggregate and the material-consumption aggregate, which share the bucketing
and grouping vocabulary."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit
from ovejitas.features.material_consumption.types import ConsumptionReason


class Bucket(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class GroupBy(StrEnum):
    ASSET = "asset"


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
