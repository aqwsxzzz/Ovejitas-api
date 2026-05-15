"""Dispatch for the generic /reports/aggregate endpoint.

Per-type builders live in builders.py. This module maps each EventType to a
builder, applies the optional ``group_by=asset`` breakdown, and wraps the
result in AggregateMeta describing how to render the rows.
"""

from collections.abc import Callable, Coroutine
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ValidationError
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.report.builders import (
    _amount_by_currency,
    _bucket_col,
    _count,
    _headcount,
    _inventory_signed,
    _quantity_by_unit,
    _scope,
)
from ovejitas.features.report.schemas import (
    AggregateMeasure,
    AggregateMeta,
    AggregateQuery,
    AggregateRow,
    GroupBy,
)


async def _headcount_by_asset(
    db: AsyncSession, farm_id: int, q: AggregateQuery
) -> list[AggregateRow]:
    """SUM(quantity) headcount, one row per (bucket, asset)."""
    b = _bucket_col(q.bucket)
    stmt = (
        select(
            b,
            Event.asset_id.label("asset_id"),
            Asset.name.label("asset_name"),
            func.sum(Event.quantity).label("value"),
        )
        .join(Asset, Asset.id == Event.asset_id)
        .where(Event.type == q.type, Event.quantity.is_not(None))
        .group_by(b, Event.asset_id, Asset.name)
        .order_by(b, Asset.name)
    )
    stmt = _scope(stmt, farm_id, q.date_from, q.date_to, q.asset_id)
    rows = (await db.execute(stmt)).all()
    return [
        AggregateRow(
            bucket=r.bucket,
            group=str(r.asset_id),
            group_label=r.asset_name,
            asset_id=r.asset_id,
            measure=AggregateMeasure.SUM_QUANTITY,
            value=Decimal(r.value),
        )
        for r in rows
    ]


Builder = Callable[[AsyncSession, int, AggregateQuery], Coroutine[Any, Any, list[AggregateRow]]]

_DISPATCH: dict[EventType, tuple[Builder, AggregateMeasure, str | None]] = {
    EventType.PRODUCTION: (_quantity_by_unit, AggregateMeasure.SUM_QUANTITY, "unit"),
    EventType.OBSERVATION: (_quantity_by_unit, AggregateMeasure.SUM_QUANTITY, "unit"),
    EventType.MORTALITY: (_headcount, AggregateMeasure.SUM_QUANTITY, None),
    EventType.ACQUISITION: (_headcount, AggregateMeasure.SUM_QUANTITY, None),
    EventType.INVENTORY: (_inventory_signed, AggregateMeasure.SUM_QUANTITY, "unit"),
    EventType.EXPENSE: (_amount_by_currency, AggregateMeasure.SUM_AMOUNT, "currency"),
    EventType.INCOME: (_amount_by_currency, AggregateMeasure.SUM_AMOUNT, "currency"),
    EventType.REPRODUCTIVE: (_count, AggregateMeasure.COUNT, None),
}

# Event types whose rows can be broken down per asset via group_by=asset.
_ASSET_GROUPABLE: frozenset[EventType] = frozenset({EventType.MORTALITY, EventType.ACQUISITION})


async def aggregate(
    db: AsyncSession, farm_id: int, q: AggregateQuery
) -> tuple[list[AggregateRow], AggregateMeta]:
    entry = _DISPATCH.get(q.type)
    if entry is None:
        raise ValidationError(f"Aggregate not supported for type={q.type.value}")
    builder, measure, group_key = entry
    if q.group_by is GroupBy.ASSET:
        if q.type not in _ASSET_GROUPABLE:
            raise ValidationError(f"group_by=asset is not supported for type={q.type.value}")
        builder = _headcount_by_asset
        group_key = "asset"
    rows = await builder(db, farm_id, q)
    meta = AggregateMeta(
        type=q.type,
        measure=measure,
        bucket=q.bucket,
        group_key=group_key,
        group_by=q.group_by,
    )
    return rows, meta
