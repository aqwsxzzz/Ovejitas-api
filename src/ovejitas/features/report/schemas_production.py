"""Schemas for the production-productivity report — produced output measured
against the target that sets what output was expected."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import Unit
from ovejitas.features.production_target.types import ProductionBasis


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
