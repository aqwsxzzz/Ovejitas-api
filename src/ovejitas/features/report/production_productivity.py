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
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.event_category.models import EventCategory
from ovejitas.features.production_target.models import AssetProductionTarget
from ovejitas.features.production_target.types import ProductionBasis, TargetPeriod
from ovejitas.features.report.productivity_math import YEAR_DAYS, convert, head_days, window_end
from ovejitas.features.report.schemas import (
    ProductionProductivityQuery,
    ProductionProductivityReport,
    ProductionProductivityRow,
)

Pair = tuple[int, int]


async def _produced(
    db: AsyncSession, farm_id: int, q: ProductionProductivityQuery
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
    stmt = apply_date_range(stmt, Event.occurred_at, q.date_from, q.date_to)
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
    db: AsyncSession, farm_id: int, q: ProductionProductivityQuery
) -> dict[Pair, AssetProductionTarget]:
    wf = q.date_from.date()
    wt = window_end(q.date_to).date()
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
    # asc order → the latest applicable effective_from wins the pair.
    return {(t.asset_id, t.category_id): t for t in (await db.execute(stmt)).scalars()}


async def _expected(
    db: AsyncSession,
    q: ProductionProductivityQuery,
    target: AssetProductionTarget,
    event_count: int,
    head_days_cache: dict[int, Decimal],
) -> Decimal:
    if target.basis is ProductionBasis.TOTAL:
        return target.expected_rate
    if target.basis is ProductionBasis.PER_EVENT:
        return target.expected_rate * event_count
    if target.asset_id not in head_days_cache:
        head_days_cache[target.asset_id] = await head_days(
            db, target.asset_id, q.date_from, q.date_to
        )
    expected = target.expected_rate * head_days_cache[target.asset_id]
    if target.period is TargetPeriod.YEAR:
        expected = expected / YEAR_DAYS
    return expected


async def _names(
    db: AsyncSession, asset_ids: set[int], category_ids: set[int]
) -> tuple[dict[int, str], dict[int, EventCategory]]:
    assets = {}
    if asset_ids:
        rows = await db.execute(select(Asset.id, Asset.name).where(Asset.id.in_(asset_ids)))
        assets = {aid: name for aid, name in rows.all()}
    categories = {}
    if category_ids:
        rows = await db.execute(select(EventCategory).where(EventCategory.id.in_(category_ids)))
        categories = {c.id: c for c in rows.scalars()}
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
    produced = await _produced(db, farm_id, q)
    targets = await _targets(db, farm_id, q)
    pairs = set(produced) | set(targets)
    asset_ids = {aid for aid, _ in pairs}
    category_ids = {cid for _, cid in pairs}
    assets, categories = await _names(db, asset_ids, category_ids)

    head_days_cache: dict[int, Decimal] = {}
    rows = []
    for asset_id, category_id in pairs:
        category = categories.get(category_id)
        if category is None:
            continue
        prod = produced.get((asset_id, category_id), {"units": {}, "count": 0})
        produced_qty = _produced_total(prod, category)
        target = targets.get((asset_id, category_id))
        expected: Decimal | None = None
        pct: Decimal | None = None
        if target is not None:
            expected = await _expected(db, q, target, prod["count"], head_days_cache)
            if expected > 0:
                pct = (produced_qty / expected * 100).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
            expected = expected.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        rows.append(
            ProductionProductivityRow(
                asset_id=asset_id,
                asset_name=assets.get(asset_id, ""),
                category_id=category_id,
                product_name=category.name,
                unit=category.unit,
                produced=produced_qty,
                expected=expected,
                productivity_pct=pct,
                basis=target.basis if target is not None else None,
                missing_capacity=target is None,
            )
        )
    rows.sort(key=lambda r: (r.asset_name, r.product_name))
    return ProductionProductivityReport(data=rows)
