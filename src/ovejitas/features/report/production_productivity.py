"""Production productivity — actual output vs expected, per (asset, product).

The product is a production ``event_category``; the expected side comes from
``asset_production_target`` rows, scaled by the target's ``basis``:

- ``per_head_continuous``: rate x animal-days (time-weighted headcount), divided
  by 365 when the period is a year.
- ``per_event``: rate x number of production events in the window.
- ``total``: the rate as the whole-window expected yield (no scaling).

Produced quantities are converted into the product's unit. Read-only, computed
live. v1 uses a single applicable target per (asset, product) window — a rate
change mid-window is not yet time-weighted across targets.
"""

from collections import defaultdict
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.event_category.models import EventCategory
from ovejitas.features.farm.timezone import farm_timezone
from ovejitas.features.production_target.models import AssetProductionTarget
from ovejitas.features.production_target.types import ProductionBasis, TargetPeriod
from ovejitas.features.report.headcount import head_days_between
from ovejitas.features.report.productivity_math import (
    YEAR_DAYS,
    Span,
    Window,
    convert,
    resolve_window,
)
from ovejitas.features.report.schemas_production import (
    ProductionProductivityQuery,
    ProductionProductivityReport,
    ProductionProductivityRow,
)

Pair = tuple[int, int]


async def _produced(
    db: AsyncSession, farm_id: int, q: ProductionProductivityQuery, window: Window
) -> dict[Pair, dict[str, Any]]:
    stmt = (
        select(
            Event.asset_id, Event.category_id, Event.unit, func.sum(Event.quantity), func.count()
        )
        .where(
            Event.farm_id == farm_id,
            Event.type == EventType.PRODUCTION,
            Event.category_id.is_not(None),
            Event.quantity.is_not(None),
        )
        .group_by(Event.asset_id, Event.category_id, Event.unit)
    )
    # The same whole-day window the denominator integrates over, not the raw
    # query bounds. Measuring a part-day numerator against a full-day expected
    # would report a flock as underperforming purely because of the hour the
    # question was asked.
    stmt = stmt.where(Event.occurred_at >= window.start, Event.occurred_at < window.end)
    if q.asset_id is not None:
        stmt = stmt.where(Event.asset_id == q.asset_id)
    if q.category_id is not None:
        stmt = stmt.where(Event.category_id == q.category_id)
    out: dict[Pair, dict[str, Any]] = defaultdict(lambda: {"units": {}, "count": 0})
    for asset_id, category_id, unit, total, count in (await db.execute(stmt)).all():
        pair = out[(asset_id, category_id)]
        pair["units"][unit] = Decimal(total)
        pair["count"] += int(count)
    return out


async def _targets(
    db: AsyncSession, farm_id: int, q: ProductionProductivityQuery, window: Window
) -> dict[Pair, list[AssetProductionTarget]]:
    # Effective dates are farm-local calendar dates, so the window has to be
    # expressed as local days too before the two can be compared — otherwise a
    # target starting on the window's first or last day is off by one at UTC-3.
    wf = window.first_day
    wt = window.last_day
    stmt = (
        select(AssetProductionTarget)
        .where(
            AssetProductionTarget.farm_id == farm_id,
            AssetProductionTarget.archived_at.is_(None),
            AssetProductionTarget.effective_from <= wt,
            or_(
                AssetProductionTarget.effective_to.is_(None),
                AssetProductionTarget.effective_to >= wf,
            ),
        )
        .order_by(AssetProductionTarget.effective_from.asc())
    )
    if q.asset_id is not None:
        stmt = stmt.where(AssetProductionTarget.asset_id == q.asset_id)
    if q.category_id is not None:
        stmt = stmt.where(AssetProductionTarget.category_id == q.category_id)
    # All targets applicable to the window, oldest first — a per_head_continuous
    # rate that changed mid-window is several rows and is time-weighted below.
    out: dict[Pair, list[AssetProductionTarget]] = defaultdict(list)
    for t in (await db.execute(stmt)).scalars():
        out[(t.asset_id, t.category_id)].append(t)
    return out


async def _continuous_expected(
    db: AsyncSession, asset: Asset, window: Window, targets: list[AssetProductionTarget]
) -> Decimal:
    """Time-weighted expected for per_head_continuous, honouring effective-dated
    rate changes: each target's rate applies over its slice of the window, and
    the animal-days in that slice are integrated at that rate."""
    expected = Decimal(0)
    for i, t in enumerate(targets):
        seg_start = max(window.start, window.local_midnight(t.effective_from))
        seg_end = window.end
        if i + 1 < len(targets):
            seg_end = min(seg_end, window.local_midnight(targets[i + 1].effective_from))
        if t.effective_to is not None:
            seg_end = min(seg_end, window.local_midnight(t.effective_to) + timedelta(days=1))
        hd = await head_days_between(db, asset, Span(seg_start, seg_end, window.tz))
        rate = t.expected_rate / YEAR_DAYS if t.period is TargetPeriod.YEAR else t.expected_rate
        expected += rate * hd
    return expected


async def _expected(
    db: AsyncSession,
    asset: Asset,
    window: Window,
    targets: list[AssetProductionTarget],
    event_count: int,
) -> Decimal:
    latest = targets[-1]
    if latest.basis is ProductionBasis.TOTAL:
        return latest.expected_rate
    if latest.basis is ProductionBasis.PER_EVENT:
        return latest.expected_rate * event_count
    return await _continuous_expected(db, asset, window, targets)


async def _names(
    db: AsyncSession, asset_ids: set[int], category_ids: set[int]
) -> tuple[dict[int, Asset], dict[int, EventCategory]]:
    # Whole Asset rows rather than names alone: the expected side also needs
    # each asset's tracking mode to know which headcount stream to read.
    assets: dict[int, Asset] = {}
    if asset_ids:
        asset_rows = await db.execute(select(Asset).where(Asset.id.in_(asset_ids)))
        assets = {a.id: a for a in asset_rows.scalars()}
    categories: dict[int, EventCategory] = {}
    if category_ids:
        cat_rows = await db.execute(select(EventCategory).where(EventCategory.id.in_(category_ids)))
        categories = {c.id: c for c in cat_rows.scalars()}
    return assets, categories


def _produced_total(produced: dict[str, Any], category: EventCategory) -> Decimal:
    if category.unit is None:
        return sum(produced["units"].values(), Decimal(0))
    return sum(
        (convert(qty, unit, category.unit) for unit, qty in produced["units"].items()),
        Decimal(0),
    )


async def production_productivity(
    db: AsyncSession, farm_id: int, q: ProductionProductivityQuery
) -> ProductionProductivityReport:
    window = resolve_window(q.date_from, q.date_to, await farm_timezone(db, farm_id))
    produced = await _produced(db, farm_id, q, window)
    targets = await _targets(db, farm_id, q, window)
    pairs = set(produced) | set(targets)
    asset_ids = {aid for aid, _ in pairs}
    category_ids = {cid for _, cid in pairs}
    assets, categories = await _names(db, asset_ids, category_ids)

    rows = []
    for asset_id, category_id in pairs:
        category = categories.get(category_id)
        asset = assets.get(asset_id)
        if category is None or asset is None:
            continue
        prod = produced.get((asset_id, category_id), {"units": {}, "count": 0})
        produced_qty = _produced_total(prod, category)
        target_list = targets.get((asset_id, category_id))
        expected: Decimal | None = None
        pct: Decimal | None = None
        if target_list:
            expected = await _expected(db, asset, window, target_list, prod["count"])
            if expected > 0:
                pct = (produced_qty / expected * 100).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
            expected = expected.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        rows.append(
            ProductionProductivityRow(
                asset_id=asset_id,
                asset_name=asset.name,
                category_id=category_id,
                product_name=category.name,
                unit=category.unit,
                produced=produced_qty,
                expected=expected,
                productivity_pct=pct,
                basis=target_list[-1].basis if target_list else None,
                missing_capacity=not target_list,
            )
        )
    rows.sort(key=lambda r: (r.asset_name, r.product_name))
    return ProductionProductivityReport(data=rows)
