"""Coop productivity — actual eggs laid vs expected, per coop (per-head model).

``expected = expected_eggs_per_head_per_day x headcount x days_in_window``.
The rate is stored on the asset; the **headcount is derived live** from the
flock's HEAD inventory events (acquisition/sale/mortality — see features/flock),
never stored. v1 uses the current headcount for the whole window (it ignores
birds added/lost mid-period); the error is zero for a stable flock. Egg counts
in ``dozen`` are normalized to single eggs (x12). Read-only; computed live, no
persistence. See docs/stories/coop-productivity.md.
"""

from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.features.asset.models import Asset, AssetKind
from ovejitas.features.event.inventory import on_hand
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, Unit
from ovejitas.features.report.schemas import (
    CoopProductivityQuery,
    CoopProductivityReport,
    CoopProductivityRow,
)

# Egg production is counted either as single eggs or by the dozen.
EGG_UNITS = (Unit.UNIT, Unit.DOZEN)


def _period_days(date_from: datetime, date_to: datetime) -> Decimal:
    # Mirror apply_date_range: a midnight date_to means "through the end of that
    # day", so roll it to the next midnight before measuring the span.
    upper = date_to + timedelta(days=1) if date_to.time() == time() else date_to
    return Decimal((upper - date_from).total_seconds()) / Decimal(86400)


async def _eggs_produced(db: AsyncSession, q: CoopProductivityQuery) -> dict[int, Decimal]:
    """Eggs laid per asset in the window, normalized to single eggs."""
    eggs = func.sum(case((Event.unit == Unit.DOZEN, Event.quantity * 12), else_=Event.quantity))
    stmt = (
        select(Event.asset_id, eggs)
        .where(
            Event.type == EventType.PRODUCTION,
            Event.unit.in_(EGG_UNITS),
            Event.quantity.is_not(None),
        )
        .group_by(Event.asset_id)
    )
    stmt = apply_date_range(stmt, Event.occurred_at, q.date_from, q.date_to)
    if q.asset_id is not None:
        stmt = stmt.where(Event.asset_id == q.asset_id)
    return {aid: Decimal(n) for aid, n in (await db.execute(stmt)).all()}


async def coop_productivity(
    db: AsyncSession, farm_id: int, q: CoopProductivityQuery
) -> CoopProductivityReport:
    days = _period_days(q.date_from, q.date_to)
    produced = await _eggs_produced(db, q)

    # Candidate coops: animal assets that either produced eggs in the window or
    # have a laying rate configured — so a configured coop with zero output
    # still shows up (at 0%) rather than silently vanishing.
    configured = Asset.expected_eggs_per_head_per_day.is_not(None)
    candidate_filter = configured if not produced else or_(configured, Asset.id.in_(list(produced)))
    stmt = select(Asset.id, Asset.name, Asset.expected_eggs_per_head_per_day).where(
        Asset.farm_id == farm_id, Asset.kind == AssetKind.ANIMAL, candidate_filter
    )
    if q.asset_id is not None:
        stmt = stmt.where(Asset.id == q.asset_id)
    candidates = (await db.execute(stmt)).all()

    rows = []
    for asset_id, name, rate in sorted(candidates, key=lambda r: r[1]):
        headcount = await on_hand(db, asset_id, Unit.HEAD)
        rows.append(_row(asset_id, name, rate, headcount, produced.get(asset_id, Decimal(0)), days))
    return CoopProductivityReport(data=rows)


def _row(
    asset_id: int,
    name: str,
    rate: Decimal | None,
    headcount: Decimal,
    produced: Decimal,
    days: Decimal,
) -> CoopProductivityRow:
    # Need both a configured rate and a recorded flock (headcount > 0) to have a
    # denominator; otherwise show what was produced and flag it.
    if rate is None or headcount <= 0:
        return CoopProductivityRow(
            asset_id=asset_id,
            asset_name=name,
            produced=produced,
            expected=None,
            productivity_pct=None,
            missing_capacity=True,
        )
    expected = rate * headcount * days
    pct = (
        (produced / expected * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        if expected > 0
        else None
    )
    return CoopProductivityRow(
        asset_id=asset_id,
        asset_name=name,
        produced=produced,
        expected=expected.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        productivity_pct=pct,
        missing_capacity=False,
    )
