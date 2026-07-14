from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit
from ovejitas.features.material_consumption.types import ConsumptionReason
from ovejitas.features.production_target.types import ProductionBasis


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


class CostPerUnitQuery(FilterParams):
    asset_id: int | None = None
    unit: Unit


class ProductionProductivityQuery(FilterParams):
    # Window required: expected output scales with the window, so there is no
    # denominator without both bounds (422 if missing).
    date_from: datetime
    date_to: datetime
    asset_id: int | None = None
    category_id: int | None = None


class ProductionProductivityRow(BaseModel):
    asset_id: int
    asset_name: str
    category_id: int
    product_name: str
    # the product's unit; produced/expected are expressed in it
    unit: Unit | None
    produced: Decimal
    # null when the (asset, product) pair has no applicable target for the window
    expected: Decimal | None
    productivity_pct: Decimal | None
    basis: ProductionBasis | None
    # true when there is no target to form a denominator — produced is still shown
    missing_capacity: bool


class ProductionProductivityReport(BaseModel):
    data: list[ProductionProductivityRow]


class UpcomingBirthsQuery(FilterParams):
    # The window is required: the report answers "which individuals are due
    # between these two dates". Overriding the optional base fields makes them
    # required query params (422 if missing), validated by FastAPI itself.
    date_from: datetime
    date_to: datetime


class UpcomingBirthRow(BaseModel):
    individual_id: int
    individual_tag: str
    asset_id: int
    expected_due_at: datetime
    offspring_count: int | None
    # whole days from the window start (date_from) to the expected due date
    days_until_due: int


class UpcomingBirthsReport(BaseModel):
    data: list[UpcomingBirthRow]


class SalesValueQuery(FilterParams):
    asset_id: int | None = None


class SalesValueRow(BaseModel):
    asset_id: int
    asset_name: str
    currency: str
    income_total: Decimal
    # unit/quantity/value are null when the asset was sold in more than one unit
    # in the window — income can't be split across units, so per-unit value is
    # undefined (ambiguous=True). The common single-unit case fills them in.
    unit: Unit | None
    quantity_sold: Decimal | None
    value_per_unit: Decimal | None
    ambiguous: bool


class SalesValueReport(BaseModel):
    data: list[SalesValueRow]


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
