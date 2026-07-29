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

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ovejitas.features.asset.models import Asset, AssetMode
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit
from ovejitas.features.individual.models import Individual
from ovejitas.features.report.productivity_math import (
    Span,
    local_day_end,
    local_midnight,
    overlap_days,
)

_ONE_DAY = Decimal(86400)


def _apply(balance: Decimal, adjustment: InventoryAdjustment, quantity: Decimal) -> Decimal:
    if adjustment is InventoryAdjustment.RESET:
        return Decimal(quantity)
    if adjustment is InventoryAdjustment.INCREMENT:
        return balance + Decimal(quantity)
    return balance - Decimal(quantity)


def _on_the_farms_calendar(
    rows: list[tuple[datetime, InventoryAdjustment, Decimal]], tz: ZoneInfo
) -> list[tuple[datetime, InventoryAdjustment, Decimal]]:
    """Move each level change onto the farm's calendar, so headcount is measured
    in whole days like everything else this report accounts in.

    The report's unit of account is a per-day rate, and its numerator counts a
    whole day's production, so an animal present for any part of a day counts
    for that day:

    - an **increment** opens its farm-local day. A coop acquired at 18:45 is
      owed a whole day's goal; prorating it to the 5¼ hours that remained
      measured a full day's production against a fifth of a day's expectation
      and reported a healthy flock at 366%.
    - a **decrement** closes its farm-local day, so animals sold or lost count
      for the day they left, matching the production already credited to them
      that morning.

    A flock bought and sold on one day therefore counts that whole day, matching
    how an individually-tracked animal is measured.

    A **RESET** keeps its exact instant — alone among the three, its direction is
    not knowable from the row. It sets the count absolutely, so whether it is a
    rise (floor) or a fall (ceil) depends on the running balance, which depends
    on the ordering this function has not yet produced. Rather than guess at a
    rule, an absolute correction is left where it was recorded.

    Shifting moves rows in both directions and can carry one past another, so the
    result is re-sorted. The sort is stable, leaving rows that land on one
    instant in their original ``occurred_at, id`` order.
    """
    moved = []
    for position, (occurred_at, adjustment, quantity) in enumerate(rows):
        when = occurred_at
        if position == 0 or adjustment is InventoryAdjustment.INCREMENT:
            # Position 0 establishes the flock, so it opens its day whatever
            # kind of row it is — there is no prior level for it to move.
            when = local_midnight(occurred_at, tz)
        elif adjustment is InventoryAdjustment.DECREMENT:
            when = local_day_end(occurred_at, tz)
        moved.append((when, adjustment, quantity))
    moved.sort(key=lambda row: row[0])
    return moved


async def _aggregated_head_days(db: AsyncSession, asset_id: int, span: Span) -> Decimal:
    """A flock: integrate HEAD inventory level changes over the span.

    Weights each headcount level by how long it held, so a mid-span change is
    counted from the moment it took effect — see ``_on_the_farms_calendar`` for
    which moments are whole-day facts rather than instants.
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
    # adjustment/quantity are nullable on Event because most event types have no
    # use for them; an INVENTORY row always carries both. Dropping any that
    # somehow lack one is the safe direction — it never invents headcount.
    rows = [
        (occurred_at, adjustment, quantity)
        for occurred_at, adjustment, quantity in (await db.execute(stmt)).all()
        if adjustment is not None and quantity is not None
    ]

    balance = Decimal(0)
    total = Decimal(0)
    cursor = span.start
    for occurred_at, adjustment, quantity in _on_the_farms_calendar(rows, span.tz):
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
        arrived = local_midnight(arrived_at, span.tz)
        left = local_day_end(min(departures), span.tz) if departures else span.end
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
