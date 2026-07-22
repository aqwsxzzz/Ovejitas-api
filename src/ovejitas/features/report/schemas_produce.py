"""Schemas for the produce-outcome report — what each producer put into a pool
and what became of it."""

from decimal import Decimal

from pydantic import BaseModel

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import Unit


class ProduceOutcomeQuery(FilterParams):
    producer_asset_id: int | None = None
    produce_asset_id: int | None = None


class ProduceOutcomeRow(BaseModel):
    producer_asset_id: int
    producer_name: str
    produce_asset_id: int
    produce_name: str
    unit: Unit
    # Everything this producer put into the pool. Not bounded by the window
    # bounds on the outflow side — see the report module.
    produced: Decimal
    sold: Decimal
    # Drawn from the pool at zero revenue: waste and spoilage today, self-use
    # once that reason exists. Produced but never earned from.
    lost: Decimal
    # Realized income for the sold quantity, in this row's currency. Null
    # currency means nothing of this producer's output has been sold yet.
    currency: str | None
    income_total: Decimal
    # True when this producer's output was sold in more than one currency, so
    # this row is one of several and the totals must not be added together.
    has_other_currency: bool


class ProduceOutcomeReport(BaseModel):
    data: list[ProduceOutcomeRow]
    # Stock that left a pool with no lot behind it — a manual inventory
    # increment, or stock carried across a reset. Reported rather than dropped
    # so the rows are never quietly incomplete.
    unattributed_quantity: Decimal
    unattributed_income: Decimal
