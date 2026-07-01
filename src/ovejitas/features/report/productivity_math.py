"""Pure-ish math for the production-productivity report: within-family unit
conversion and time-weighted headcount (animal-days) over a window.

Kept separate from the report orchestration so the fiddly bits are small and
independently testable.
"""

from datetime import datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit

YEAR_DAYS = Decimal(365)

# Size of one unit in its family's base unit (count=unit, volume=ml, mass=g).
# Same-family membership is guaranteed for stored production events by the
# event guard, so conversion is always within one of these scales.
_BASE_SIZE: dict[Unit, Decimal] = {
    Unit.UNIT: Decimal(1),
    Unit.DOZEN: Decimal(12),
    Unit.ML: Decimal(1),
    Unit.L: Decimal(1000),
    Unit.GAL: Decimal("3785.411784"),
    Unit.G: Decimal(1),
    Unit.KG: Decimal(1000),
    Unit.LB: Decimal("453.59237"),
    Unit.T: Decimal(1_000_000),
}


def convert(quantity: Decimal, from_unit: Unit, to_unit: Unit) -> Decimal:
    """Convert a quantity between two units of the same measurement family."""
    if from_unit == to_unit:
        return quantity
    return quantity * _BASE_SIZE[from_unit] / _BASE_SIZE[to_unit]


def window_end(date_to: datetime) -> datetime:
    """Mirror apply_date_range: a midnight upper bound means 'through that day'."""
    return date_to + timedelta(days=1) if date_to.time() == time() else date_to


def _apply(balance: Decimal, adjustment: InventoryAdjustment, quantity: Decimal) -> Decimal:
    if adjustment is InventoryAdjustment.RESET:
        return Decimal(quantity)
    if adjustment is InventoryAdjustment.INCREMENT:
        return balance + Decimal(quantity)
    return balance - Decimal(quantity)


async def head_days(
    db: AsyncSession, asset_id: int, date_from: datetime, date_to: datetime
) -> Decimal:
    """Animal-days: the integral of HEAD headcount over [date_from, window_end).

    Unlike a snapshot, this weights each headcount level by how long it held,
    so births/deaths/sales mid-window are counted correctly.
    """
    upper = window_end(date_to)
    base = (
        select(Event.occurred_at, Event.adjustment, Event.quantity)
        .where(
            Event.asset_id == asset_id,
            Event.type == EventType.INVENTORY,
            Event.unit == Unit.HEAD,
        )
        .order_by(Event.occurred_at.asc(), Event.id.asc())
    )
    rows = (await db.execute(base)).all()

    balance = Decimal(0)
    total = Decimal(0)
    cursor = date_from
    for occurred_at, adjustment, quantity in rows:
        if occurred_at < date_from:
            balance = _apply(balance, adjustment, quantity)
            continue
        if occurred_at >= upper:
            break
        total += balance * Decimal((occurred_at - cursor).total_seconds()) / Decimal(86400)
        balance = _apply(balance, adjustment, quantity)
        cursor = occurred_at
    total += balance * Decimal((upper - cursor).total_seconds()) / Decimal(86400)
    return total
