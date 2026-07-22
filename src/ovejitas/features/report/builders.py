"""Per-type builders for the generic /reports/aggregate endpoint.

Each builder turns events of one EventType into a stream of
AggregateRow{bucket, group, measure, value}. Dispatch lives in aggregate.py.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.features.currency.models import Currency
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, InventoryAdjustment
from ovejitas.features.report.schemas_aggregate import (
    AggregateMeasure,
    AggregateQuery,
    AggregateRow,
    Bucket,
)


def _scope(
    stmt: Select[Any],
    farm_id: int,
    date_from: datetime | None,
    date_to: datetime | None,
    asset_id: int | None,
) -> Select[Any]:
    stmt = stmt.where(Event.farm_id == farm_id)
    stmt = apply_date_range(stmt, Event.occurred_at, date_from, date_to)
    if asset_id is not None:
        stmt = stmt.where(Event.asset_id == asset_id)
    return stmt


def _bucket_col(bucket: Bucket) -> Any:
    return func.date_trunc(bucket.value, Event.occurred_at).label("bucket")


async def _quantity_by_unit(
    db: AsyncSession, farm_id: int, q: AggregateQuery
) -> list[AggregateRow]:
    b = _bucket_col(q.bucket)
    stmt = (
        select(b, Event.unit.label("unit"), func.sum(Event.quantity).label("value"))
        .where(
            Event.type == q.type,
            Event.quantity.is_not(None),
            Event.unit.is_not(None),
        )
        .group_by(b, Event.unit)
        .order_by(b, Event.unit)
    )
    stmt = _scope(stmt, farm_id, q.date_from, q.date_to, q.asset_id)
    if q.unit is not None:
        stmt = stmt.where(Event.unit == q.unit)
    rows = (await db.execute(stmt)).all()
    return [
        AggregateRow(
            bucket=r.bucket,
            group=r.unit.value,
            measure=AggregateMeasure.SUM_QUANTITY,
            value=Decimal(r.value),
        )
        for r in rows
    ]


async def _headcount(db: AsyncSession, farm_id: int, q: AggregateQuery) -> list[AggregateRow]:
    b = _bucket_col(q.bucket)
    stmt = (
        select(b, func.sum(Event.quantity).label("value"))
        .where(Event.type == q.type, Event.quantity.is_not(None))
        .group_by(b)
        .order_by(b)
    )
    stmt = _scope(stmt, farm_id, q.date_from, q.date_to, q.asset_id)
    rows = (await db.execute(stmt)).all()
    return [
        AggregateRow(
            bucket=r.bucket,
            group=None,
            measure=AggregateMeasure.SUM_QUANTITY,
            value=Decimal(r.value),
        )
        for r in rows
    ]


async def _inventory_signed(
    db: AsyncSession, farm_id: int, q: AggregateQuery
) -> list[AggregateRow]:
    """Net flow within window. Resets excluded unless explicitly filtered for."""
    b = _bucket_col(q.bucket)
    if q.adjustment is None:
        value = func.sum(
            case(
                (Event.adjustment == InventoryAdjustment.INCREMENT, Event.quantity),
                (Event.adjustment == InventoryAdjustment.DECREMENT, -Event.quantity),
                else_=Decimal(0),
            )
        ).label("value")
        stmt = select(b, Event.unit.label("unit"), value).where(
            Event.type == EventType.INVENTORY,
            Event.adjustment.in_([InventoryAdjustment.INCREMENT, InventoryAdjustment.DECREMENT]),
        )
    else:
        stmt = select(b, Event.unit.label("unit"), func.sum(Event.quantity).label("value")).where(
            Event.type == EventType.INVENTORY, Event.adjustment == q.adjustment
        )
    stmt = stmt.group_by(b, Event.unit).order_by(b, Event.unit)
    stmt = _scope(stmt, farm_id, q.date_from, q.date_to, q.asset_id)
    if q.unit is not None:
        stmt = stmt.where(Event.unit == q.unit)
    rows = (await db.execute(stmt)).all()
    return [
        AggregateRow(
            bucket=r.bucket,
            group=r.unit.value,
            measure=AggregateMeasure.SUM_QUANTITY,
            value=Decimal(r.value or 0),
        )
        for r in rows
    ]


async def _amount_by_currency(
    db: AsyncSession, farm_id: int, q: AggregateQuery
) -> list[AggregateRow]:
    b = _bucket_col(q.bucket)
    stmt = (
        select(b, Currency.code.label("currency"), func.sum(Event.amount).label("value"))
        .join(Currency, Currency.id == Event.currency_id)
        .where(
            Event.type == q.type,
            Event.amount.is_not(None),
            Event.currency_id.is_not(None),
        )
        .group_by(b, Currency.code)
        .order_by(b, Currency.code)
    )
    stmt = _scope(stmt, farm_id, q.date_from, q.date_to, q.asset_id)
    if q.currency is not None:
        stmt = stmt.where(Currency.code == q.currency)
    rows = (await db.execute(stmt)).all()
    return [
        AggregateRow(
            bucket=r.bucket,
            group=r.currency,
            measure=AggregateMeasure.SUM_AMOUNT,
            value=Decimal(r.value),
        )
        for r in rows
    ]


async def _count(db: AsyncSession, farm_id: int, q: AggregateQuery) -> list[AggregateRow]:
    b = _bucket_col(q.bucket)
    stmt = (
        select(b, func.count().label("value")).where(Event.type == q.type).group_by(b).order_by(b)
    )
    stmt = _scope(stmt, farm_id, q.date_from, q.date_to, q.asset_id)
    rows = (await db.execute(stmt)).all()
    return [
        AggregateRow(
            bucket=r.bucket,
            group=None,
            measure=AggregateMeasure.COUNT,
            value=Decimal(r.value),
        )
        for r in rows
    ]
