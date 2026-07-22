"""Sales value — the realized average price per unit sold, per asset.

For each asset sold via the ``material_sale`` action in the window:
``value_per_unit = total sale income / total quantity sold``. This is the
weighted-average price actually received (eggs are the textbook fungible case),
derived from the paired INCOME + INVENTORY-decrement events the action emits —
no stored unit price. Read-only; computed live. See docs/stories/egg-valuation.md.
"""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.features.asset.models import Asset
from ovejitas.features.currency.models import Currency
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit
from ovejitas.features.report.schemas_profitability import (
    SalesValueQuery,
    SalesValueReport,
    SalesValueRow,
)

# Both events a sale emits are tagged with this source; pairing income to
# quantity through it keeps non-sale income (manual entries) out of the average.
_SALE_SOURCE = "material_sale"


async def _income_by_asset(
    db: AsyncSession, farm_id: int, q: SalesValueQuery
) -> list[tuple[int, str, str, Decimal]]:
    """(asset_id, asset_name, currency, income_total) for material-sale income."""
    stmt = (
        select(Asset.id, Asset.name, Currency.code, func.sum(Event.amount))
        .join(Asset, Asset.id == Event.asset_id)
        .join(Currency, Currency.id == Event.currency_id)
        .where(
            Asset.farm_id == farm_id,
            Event.type == EventType.INCOME,
            Event.payload["source"].astext == _SALE_SOURCE,
            Event.amount.is_not(None),
            Event.currency_id.is_not(None),
        )
        .group_by(Asset.id, Asset.name, Currency.code)
    )
    stmt = apply_date_range(stmt, Event.occurred_at, q.date_from, q.date_to)
    if q.asset_id is not None:
        stmt = stmt.where(Asset.id == q.asset_id)
    return [
        (aid, name, cur, Decimal(total)) for aid, name, cur, total in (await db.execute(stmt)).all()
    ]


async def _quantity_by_asset_unit(
    db: AsyncSession, farm_id: int, q: SalesValueQuery
) -> dict[int, dict[Unit, Decimal]]:
    """{asset_id: {unit: quantity_sold}} for material-sale inventory decrements."""
    stmt = (
        select(Event.asset_id, Event.unit, func.sum(Event.quantity))
        .where(
            Event.farm_id == farm_id,
            Event.type == EventType.INVENTORY,
            Event.adjustment == InventoryAdjustment.DECREMENT,
            Event.payload["source"].astext == _SALE_SOURCE,
            Event.quantity.is_not(None),
        )
        .group_by(Event.asset_id, Event.unit)
    )
    stmt = apply_date_range(stmt, Event.occurred_at, q.date_from, q.date_to)
    if q.asset_id is not None:
        stmt = stmt.where(Event.asset_id == q.asset_id)
    by_asset: dict[int, dict[Unit, Decimal]] = defaultdict(dict)
    for asset_id, unit, qty in (await db.execute(stmt)).all():
        by_asset[asset_id][unit] = Decimal(qty)
    return by_asset


def _row(
    asset_id: int, name: str, currency: str, income: Decimal, units: dict[Unit, Decimal]
) -> SalesValueRow:
    # Income carries no unit, so it can only be divided into a per-unit value
    # when the asset was sold in exactly one unit in the window.
    if len(units) == 1:
        unit, qty = next(iter(units.items()))
        value = (
            (income / qty).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if qty > 0 else None
        )
        return SalesValueRow(
            asset_id=asset_id,
            asset_name=name,
            currency=currency,
            income_total=income,
            unit=unit,
            quantity_sold=qty,
            value_per_unit=value,
            ambiguous=value is None,
        )
    return SalesValueRow(
        asset_id=asset_id,
        asset_name=name,
        currency=currency,
        income_total=income,
        unit=None,
        quantity_sold=None,
        value_per_unit=None,
        ambiguous=True,
    )


async def sales_value(db: AsyncSession, farm_id: int, q: SalesValueQuery) -> SalesValueReport:
    income = await _income_by_asset(db, farm_id, q)
    if not income:
        return SalesValueReport(data=[])
    quantity = await _quantity_by_asset_unit(db, farm_id, q)
    rows = [
        _row(asset_id, name, currency, total, quantity.get(asset_id, {}))
        for asset_id, name, currency, total in sorted(income, key=lambda r: (r[1], r[2]))
    ]
    return SalesValueReport(data=rows)
