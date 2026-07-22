"""R5 inventory summary — current on-hand stock per (asset, unit).

On-hand is derived by replaying INVENTORY events: increments minus decrements
since the most recent reset. Read-only.
"""

from collections import defaultdict
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.filters import apply_date_range
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, InventoryAdjustment
from ovejitas.features.report.schemas_inventory import InventorySummaryQuery, InventorySummaryRow


async def inventory_summary(
    db: AsyncSession, farm_id: int, q: InventorySummaryQuery
) -> list[InventorySummaryRow]:
    stmt = (
        select(
            Event.asset_id,
            Asset.name.label("asset_name"),
            Event.adjustment,
            Event.unit,
            Event.quantity,
        )
        .join(Asset, Asset.id == Event.asset_id)
        .where(
            Asset.farm_id == farm_id,
            Event.type == EventType.INVENTORY,
        )
        .order_by(Event.asset_id, Event.occurred_at.asc(), Event.id.asc())
    )
    # On-hand is a running balance — it must replay the full event history,
    # so date_from must NOT truncate it (dropping a prior RESET would make
    # the replay start mid-stream). date_to is an honest upper bound: the
    # balance "as of" that moment.
    stmt = apply_date_range(stmt, Event.occurred_at, None, q.date_to)
    if q.asset_id is not None:
        stmt = stmt.where(Event.asset_id == q.asset_id)
    rows = (await db.execute(stmt)).all()

    buckets: dict[tuple[int, Any], dict[str, Any]] = defaultdict(
        lambda: {"on_hand": Decimal(0), "asset_name": ""}
    )
    for asset_id, asset_name, adjustment, unit, quantity in rows:
        bucket = buckets[(asset_id, unit)]
        bucket["asset_name"] = asset_name
        if adjustment is InventoryAdjustment.RESET:
            bucket["on_hand"] = Decimal(quantity)
        elif adjustment is InventoryAdjustment.INCREMENT:
            bucket["on_hand"] = Decimal(bucket["on_hand"]) + Decimal(quantity)
        elif adjustment is InventoryAdjustment.DECREMENT:
            bucket["on_hand"] = Decimal(bucket["on_hand"]) - Decimal(quantity)
    return [
        InventorySummaryRow(
            asset_id=asset_id,
            asset_name=vals["asset_name"],
            unit=unit,
            on_hand=Decimal(vals["on_hand"]),
        )
        for (asset_id, unit), vals in sorted(
            buckets.items(), key=lambda kv: (kv[1]["asset_name"], kv[0][1].value)
        )
    ]
