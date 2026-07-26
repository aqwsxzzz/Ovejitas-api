"""Pure-ish math for the production-productivity report: within-family unit
conversion and time-weighted headcount (animal-days) over a window.

Kept separate from the report orchestration so the fiddly bits are small and
independently testable.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

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


@dataclass(frozen=True)
class Window:
    """A productivity window resolved onto the farm's calendar.

    A whole number of calendar days: ``start`` is the midnight opening
    ``date_from``'s day, ``end`` the exclusive midnight closing ``date_to``'s.
    Both the produced numerator and the animal-day denominator are bounded by
    these same two instants, so the two halves of the ratio can never disagree
    about which days they cover.
    """

    start: datetime
    end: datetime
    tz: ZoneInfo

    @property
    def first_day(self) -> date:
        """First farm-local calendar day the window touches."""
        return self.start.astimezone(self.tz).date()

    @property
    def last_day(self) -> date:
        """Last farm-local calendar day the window touches (``end`` is exclusive)."""
        return (self.end - timedelta(microseconds=1)).astimezone(self.tz).date()

    def local_midnight(self, day: date) -> datetime:
        """The instant calendar day ``day`` opens on the farm.

        Effective-dated target rows store bare calendar dates — a farmer saying
        "this rate applies from the 10th" means the 10th where the animals are.
        Reading one as UTC midnight starts the rate three hours early at UTC-3,
        which silently mis-weights every animal-day in the first segment.
        """
        return datetime(day.year, day.month, day.day, tzinfo=self.tz)


def resolve_window(date_from: datetime, date_to: datetime, tz: ZoneInfo) -> Window:
    """Widen the bounds to the whole calendar days they fall on.

    The report is day-grained — a target is a per-day (or per-year) rate — so
    both ends snap to day boundaries. Asking about today at 18:45 must expect a
    whole day's goal: with the lower bound left raw, a 500-head flock at 1/head
    expects 109 rather than 500, because only 5¼ hours of the day remain to
    integrate over. The same reasoning closes the upper bound at the *end* of
    ``date_to``'s day, so an in-progress day is never prorated to elapsed hours.

    Both ends snap in the bound's own frame, matching ``apply_date_range``:
    after localization a naive bound already carries the farm's zone, and an
    explicit offset is the client naming a frame deliberately. ``tz`` is carried
    separately because target rows store bare dates that have no frame of their
    own — see ``local_midnight``.
    """
    start = datetime.combine(date_from.date(), time(), tzinfo=date_from.tzinfo)
    last_day_start = datetime.combine(date_to.date(), time(), tzinfo=date_to.tzinfo)
    return Window(start=start, end=last_day_start + timedelta(days=1), tz=tz)


def _apply(balance: Decimal, adjustment: InventoryAdjustment, quantity: Decimal) -> Decimal:
    if adjustment is InventoryAdjustment.RESET:
        return Decimal(quantity)
    if adjustment is InventoryAdjustment.INCREMENT:
        return balance + Decimal(quantity)
    return balance - Decimal(quantity)


async def head_days_between(
    db: AsyncSession, asset_id: int, start: datetime, end: datetime
) -> Decimal:
    """Animal-days: the integral of HEAD headcount over the half-open [start, end).

    Weights each headcount level by how long it held, so births/deaths/sales
    inside the interval are counted correctly. ``start``/``end`` are exact bounds
    (no whole-day rolling — the caller decides them).
    """
    if end <= start:
        return Decimal(0)
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
    cursor = start
    for occurred_at, adjustment, quantity in rows:
        if occurred_at < start:
            balance = _apply(balance, adjustment, quantity)
            continue
        if occurred_at >= end:
            break
        total += balance * Decimal((occurred_at - cursor).total_seconds()) / Decimal(86400)
        balance = _apply(balance, adjustment, quantity)
        cursor = occurred_at
    total += balance * Decimal((end - cursor).total_seconds()) / Decimal(86400)
    return total
