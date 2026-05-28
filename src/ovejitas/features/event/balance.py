"""Derived per-unit on-hand balance for one asset, replayed from its INVENTORY
events. A read-only projection — kept separate from EventService's write path.
"""

from collections import defaultdict
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.schemas import InventoryBalance, InventoryBalanceRow
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit


async def asset_has_events(db: AsyncSession, asset_id: int) -> bool:
    """True if any event is attached to the asset — used to freeze structural
    asset fields (kind/mode) once history exists."""
    stmt = select(Event.id).where(Event.asset_id == asset_id).limit(1)
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def compute_inventory_balance(db: AsyncSession, asset: Asset) -> InventoryBalance:
    """Replay the asset's INVENTORY events into an on-hand balance per unit."""
    stmt = (
        select(Event.adjustment, Event.unit, Event.quantity, Event.occurred_at)
        .where(
            Event.asset_id == asset.id,
            Event.type == EventType.INVENTORY,
        )
        .order_by(Event.occurred_at.asc(), Event.id.asc())
    )
    rows = (await db.execute(stmt)).all()
    by_unit: dict[Unit, dict[str, Any]] = defaultdict(
        lambda: {"on_hand": Decimal(0), "last_reset_at": None}
    )
    for adjustment, unit, quantity, occurred_at in rows:
        bucket = by_unit[unit]
        if adjustment is InventoryAdjustment.RESET:
            bucket["on_hand"] = Decimal(quantity)
            bucket["last_reset_at"] = occurred_at
        elif adjustment is InventoryAdjustment.INCREMENT:
            bucket["on_hand"] = bucket["on_hand"] + Decimal(quantity)
        elif adjustment is InventoryAdjustment.DECREMENT:
            bucket["on_hand"] = bucket["on_hand"] - Decimal(quantity)
    balances = [
        InventoryBalanceRow(
            unit=unit,
            on_hand=vals["on_hand"],
            last_reset_at=vals["last_reset_at"],
        )
        for unit, vals in sorted(by_unit.items(), key=lambda kv: kv[0].value)
    ]
    return InventoryBalance(asset_id=asset.id, balances=balances)
