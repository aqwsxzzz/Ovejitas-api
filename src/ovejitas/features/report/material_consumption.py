"""Time-bucketed aggregate over the material_consumption table.

Backs GET /reports/material-consumption-aggregate. Reuses the generic
``AggregateRow`` shape; quantities are grouped by unit since units never sum.
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import RowMapping, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ovejitas.core.filters import apply_date_range
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.types import Unit
from ovejitas.features.material_consumption.models import MaterialConsumption
from ovejitas.features.report.schemas_aggregate import (
    AggregateMeasure,
    AggregateRow,
    ConsumptionGroupBy,
    MaterialConsumptionAggregateQuery,
    MaterialConsumptionAggregateTotal,
)

_material = aliased(Asset, name="material")
_consumer = aliased(Asset, name="consumer")


def _build_query(farm_id: int, q: MaterialConsumptionAggregateQuery) -> Select[Any]:
    bucket = func.date_trunc(q.bucket.value, MaterialConsumption.occurred_at).label("bucket")
    selected: list[Any] = [
        bucket,
        MaterialConsumption.unit.label("unit"),
        func.sum(MaterialConsumption.quantity).label("value"),
    ]
    group_cols: list[Any] = [bucket, MaterialConsumption.unit]
    if q.group_by in (ConsumptionGroupBy.MATERIAL, ConsumptionGroupBy.BOTH):
        selected += [
            MaterialConsumption.material_asset_id.label("material_id"),
            _material.name.label("material_name"),
        ]
        group_cols += [MaterialConsumption.material_asset_id, _material.name]
    if q.group_by in (ConsumptionGroupBy.CONSUMER, ConsumptionGroupBy.BOTH):
        selected += [
            MaterialConsumption.consumer_asset_id.label("consumer_id"),
            _consumer.name.label("consumer_name"),
        ]
        group_cols += [MaterialConsumption.consumer_asset_id, _consumer.name]

    stmt = (
        select(*selected)
        .select_from(MaterialConsumption)
        .join(_material, _material.id == MaterialConsumption.material_asset_id)
        .outerjoin(_consumer, _consumer.id == MaterialConsumption.consumer_asset_id)
        .where(MaterialConsumption.farm_id == farm_id)
    )
    stmt = apply_date_range(stmt, MaterialConsumption.occurred_at, q.date_from, q.date_to)
    if q.material_asset_id is not None:
        stmt = stmt.where(MaterialConsumption.material_asset_id == q.material_asset_id)
    if q.consumer_asset_id is not None:
        stmt = stmt.where(MaterialConsumption.consumer_asset_id == q.consumer_asset_id)
    if q.reason is not None:
        stmt = stmt.where(MaterialConsumption.reason == q.reason)
    return stmt.group_by(*group_cols).order_by(bucket)


def _to_row(group_by: ConsumptionGroupBy, r: RowMapping) -> AggregateRow:
    group: str | None
    label: str | None
    if group_by is ConsumptionGroupBy.MATERIAL:
        group, label = str(r["material_id"]), r["material_name"]
    elif group_by is ConsumptionGroupBy.CONSUMER:
        cid = r["consumer_id"]
        group = str(cid) if cid is not None else None
        label = r["consumer_name"]
    else:
        cid = r["consumer_id"]
        group = f"{r['material_id']}:{cid if cid is not None else ''}"
        label = f"{r['material_name']} → {r['consumer_name'] or '—'}"
    return AggregateRow(
        bucket=r["bucket"],
        group=group,
        group_label=label,
        measure=AggregateMeasure.SUM_QUANTITY,
        value=Decimal(r["value"]),
        unit=r["unit"],
    )


def _totals(rows: list[AggregateRow]) -> list[MaterialConsumptionAggregateTotal]:
    acc: dict[tuple[str | None, Unit], dict[str, Any]] = {}
    for row in rows:
        assert row.unit is not None
        key = (row.group, row.unit)
        entry = acc.setdefault(key, {"label": row.group_label, "total": Decimal(0)})
        entry["total"] += row.value
    return [
        MaterialConsumptionAggregateTotal(
            group=group, group_label=entry["label"], unit=unit, total_qty=entry["total"]
        )
        for (group, unit), entry in sorted(
            acc.items(), key=lambda kv: (kv[0][0] or "", kv[0][1].value)
        )
    ]


async def material_consumption_aggregate(
    db: AsyncSession, farm_id: int, q: MaterialConsumptionAggregateQuery
) -> tuple[list[AggregateRow], list[MaterialConsumptionAggregateTotal]]:
    result = (await db.execute(_build_query(farm_id, q))).mappings().all()
    rows = [_to_row(q.group_by, r) for r in result]
    return rows, _totals(rows)
