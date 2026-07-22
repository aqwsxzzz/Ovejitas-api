"""Schemas for the money reports — profitability, profitability-full, cost per
produced unit, and realized sale value. Every row is scoped to one currency;
currencies are never summed."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import Unit


class ProfitabilityQuery(FilterParams):
    asset_id: int | None = None


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


class ProfitabilityFullQuery(FilterParams):
    asset_id: int | None = None


class ProfitabilityFullRow(BaseModel):
    asset_id: int
    asset_name: str
    # the currency this row is valued in (like R1). Null only for an asset whose
    # sole activity is unvalued feed — it has no currency in any ledger.
    currency: str | None
    income_total: Decimal
    # This asset's share of what its produce earned when the pool it harvests
    # into was sold, derived by a FIFO draw over the contributing lots. Kept
    # separate from income_total: that money is booked on the produce asset, not
    # here, and conflating the two would hide which is which.
    allocated_produce_income: Decimal
    direct_expense_total: Decimal
    # feed consumed by the asset, valued at average purchase cost in this row's
    # currency (R3 basis). A mixed-currency material splits across currency rows.
    consumed_material_cost: Decimal
    total_cost: Decimal
    # income - direct expense only (excludes feed AND allocated produce income)
    # — kept unchanged so existing profitability (R1) consumers see the same
    # figure. The bottom line that counts produce income is net_incl_materials.
    net: Decimal
    # (income + allocated produce income) - (direct expense + feed) — the "real"
    # bottom line per asset, in this row's currency; currencies are never mixed
    net_incl_materials: Decimal
    # true when feed the asset consumed has no purchase basis in ANY currency, so
    # consumed_material_cost is understated rather than hidden
    has_unvalued_consumption: bool


class ProfitabilityFullTotal(BaseModel):
    currency: str
    income_total: Decimal
    allocated_produce_income: Decimal
    direct_expense_total: Decimal
    consumed_material_cost: Decimal
    total_cost: Decimal
    net: Decimal
    net_incl_materials: Decimal


class ProfitabilityFullReport(BaseModel):
    data: list[ProfitabilityFullRow]
    totals: list[ProfitabilityFullTotal]


class CostPerUnitQuery(FilterParams):
    asset_id: int | None = None
    unit: Unit


class CostPerUnitRow(BaseModel):
    asset_id: int
    asset_name: str
    # the currency this row's cost is expressed in. Null only for a producer with
    # no cost in any currency (no direct expense, no valued feed).
    currency: str | None
    production_quantity: Decimal
    direct_expense_total: Decimal
    # feed valued at average purchase cost in this row's currency; a producer fed
    # from a mixed-currency material gets one row per currency
    consumed_material_cost: Decimal
    total_cost: Decimal
    # cost_per_unit in this row's currency; null when the producer made nothing in
    # the window (no divide-by-zero)
    cost_per_unit: Decimal | None
    # true when feed it consumed has no purchase history in ANY currency — the
    # cost is then understated and the row says so rather than hide it
    has_unvalued_consumption: bool


class CostPerUnitReport(BaseModel):
    data: list[CostPerUnitRow]
    unit: Unit


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
