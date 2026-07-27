"""Animal-days: how many head an asset carried, integrated over a span.

The expected side of the production-productivity report is a rate times a
headcount held over time, so this module answers one question — "how many
animals were here, and for how long?" — for both ways the domain records that.

Two shapes, deliberately kept as two functions rather than one integral with a
mode flag: a flock is an event stream of level changes to a single pool, an
individual herd is a set of rows each with its own arrival and departure. Same
answer, unrelated derivations.

The two are mutually exclusive by construction, so neither can double-count the
other: flock actions require an aggregated asset (``flock/guards.py``),
individuals require an individual one (``individual/service.py``), and the
generic event router refuses INVENTORY on an individual-mode animal
(``event/guards.py``).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ovejitas.features.asset.models import Asset, AssetMode
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit
from ovejitas.features.individual.models import Individual

_ONE_DAY = Decimal(86400)


@dataclass(frozen=True)
class Span:
    """A half-open [start, end) interval to integrate headcount over, plus the
    farm's zone.

    Distinct from ``Window``: a window is a whole number of calendar days, while
    a span is that window clipped to one target's effective dates and so may
    open or close mid-day. The zone travels with it because both branches
    resolve day boundaries on the farm's calendar, not UTC's.
    """

    start: datetime
    end: datetime
    tz: ZoneInfo


def _local_midnight(moment: datetime, tz: ZoneInfo) -> datetime:
    """The instant the farm-local calendar day containing ``moment`` opens."""
    local = moment.astimezone(tz)
    return datetime(local.year, local.month, local.day, tzinfo=tz)


def _apply(balance: Decimal, adjustment: InventoryAdjustment, quantity: Decimal) -> Decimal:
    if adjustment is InventoryAdjustment.RESET:
        return Decimal(quantity)
    if adjustment is InventoryAdjustment.INCREMENT:
        return balance + Decimal(quantity)
    return balance - Decimal(quantity)


def overlap_days(start: datetime, end: datetime, span: Span) -> Decimal:
    """Days of [start, end) that fall inside ``span``. Pure; zero if disjoint."""
    first = max(start, span.start)
    last = min(end, span.end)
    if last <= first:
        return Decimal(0)
    return Decimal((last - first).total_seconds()) / _ONE_DAY


async def _aggregated_head_days(db: AsyncSession, asset_id: int, span: Span) -> Decimal:
    """A flock: integrate HEAD inventory level changes over the span.

    Weights each headcount level by how long it held, so acquisitions, sales and
    deaths inside the span are counted at the moment they happened.

    One event is not a level change: the asset's very first HEAD event, which
    establishes the flock rather than moving an existing headcount. It counts
    from the start of its farm-local day. A coop acquired at 18:45 is owed a
    whole day's goal — prorating it to the 5¼ hours that remained measured a
    full day's production against a fifth of a day's expectation and reported a
    healthy flock at 366%.

    "First" is the earliest HEAD event the asset has ever recorded, not the
    earliest one inside the span — otherwise the same day would be billed
    differently depending on which window asked about it.
    """
    if span.end <= span.start:
        return Decimal(0)
    stmt = (
        select(Event.occurred_at, Event.adjustment, Event.quantity)
        .where(
            Event.asset_id == asset_id,
            Event.type == EventType.INVENTORY,
            Event.unit == Unit.HEAD,
        )
        .order_by(Event.occurred_at.asc(), Event.id.asc())
    )
    rows = (await db.execute(stmt)).all()

    balance = Decimal(0)
    total = Decimal(0)
    cursor = span.start
    for position, (occurred_at, adjustment, quantity) in enumerate(rows):
        if position == 0:
            # Unfiltered by the span, so this really is the establishing event.
            occurred_at = _local_midnight(occurred_at, span.tz)
        if occurred_at < span.start:
            balance = _apply(balance, adjustment, quantity)
            continue
        if occurred_at >= span.end:
            break
        total += balance * Decimal((occurred_at - cursor).total_seconds()) / _ONE_DAY
        balance = _apply(balance, adjustment, quantity)
        cursor = occurred_at
    total += balance * Decimal((span.end - cursor).total_seconds()) / _ONE_DAY
    return total


async def _individual_head_days(db: AsyncSession, asset_id: int, span: Span) -> Decimal:
    """An individually-tracked herd: sum each animal's presence over the span.

    Every individual carries an acquisition event whatever brought it here —
    purchased, born, or other — so arrival is uniform across creation paths.
    Departure is its mortality or sale event; an animal with neither is still
    here.

    Both ends resolve to whole farm-local days: an animal counts from the start
    of the day it arrived and through the end of the day it left. The report's
    unit of account is a per-day rate, and a cow bought at 18:45 or sold at 08:00
    still has that day's production credited to her — prorating her presence
    while counting her output whole is the mismatch this avoids. Unlike a flock,
    where one event carries all 500 head, a herd is one arrival per animal, so
    every arrival gets this treatment rather than only the first.
    """
    if span.end <= span.start:
        return Decimal(0)
    acquisition = aliased(Event)
    mortality = aliased(Event)
    sale = aliased(Event)
    stmt = (
        select(acquisition.occurred_at, mortality.occurred_at, sale.occurred_at)
        .select_from(Individual)
        .join(acquisition, acquisition.id == Individual.acquisition_event_id)
        .outerjoin(mortality, mortality.id == Individual.mortality_event_id)
        .outerjoin(sale, sale.id == Individual.sale_event_id)
        .where(Individual.asset_id == asset_id)
    )
    total = Decimal(0)
    for arrived_at, died_at, sold_at in (await db.execute(stmt)).all():
        # Status is single-valued so at most one departure is set; taking the
        # earlier of the two is only defensive.
        departures = [moment for moment in (died_at, sold_at) if moment is not None]
        arrived = _local_midnight(arrived_at, span.tz)
        left = (
            _local_midnight(min(departures), span.tz) + timedelta(days=1)
            if departures
            else span.end
        )
        total += overlap_days(arrived, left, span)
    return total


async def head_days_between(db: AsyncSession, asset: Asset, span: Span) -> Decimal:
    """Animal-days the asset carried over ``span``, however it records headcount.

    Anything that is not an individual-mode asset — including an animal whose
    mode was never set, which can hold neither individuals nor flock inventory —
    reads the inventory stream and so keeps returning exactly what it does today.
    """
    if asset.mode is AssetMode.INDIVIDUAL:
        return await _individual_head_days(db, asset.id, span)
    return await _aggregated_head_days(db, asset.id, span)
