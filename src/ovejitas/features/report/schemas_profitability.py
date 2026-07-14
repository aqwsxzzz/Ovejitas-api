from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from ovejitas.core.filters import FilterParams


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
    # always the farm default currency — this report is single-currency
    currency: str
    income_total: Decimal
    direct_expense_total: Decimal
    # feed consumed by the asset, valued at average purchase cost (R3 basis)
    consumed_material_cost: Decimal
    total_cost: Decimal
    # income - direct expense only (excludes feed) — kept unchanged so existing
    # profitability consumers see the same figure
    net: Decimal
    # income - (direct expense + feed) — the "real" bottom line per asset
    net_incl_materials: Decimal
    # true when feed it consumed has no purchase basis in the farm currency, so
    # consumed_material_cost is understated rather than hidden
    has_unvalued_consumption: bool
    # true when the asset also had income/expense in another currency, excluded
    # from this single-currency report rather than silently converted
    has_other_currency: bool


class ProfitabilityFullTotal(BaseModel):
    currency: str
    income_total: Decimal
    direct_expense_total: Decimal
    consumed_material_cost: Decimal
    total_cost: Decimal
    net: Decimal
    net_incl_materials: Decimal


class ProfitabilityFullReport(BaseModel):
    data: list[ProfitabilityFullRow]
    totals: list[ProfitabilityFullTotal]
