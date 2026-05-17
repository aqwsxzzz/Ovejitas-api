"""Stock-mutation helper backing material consumptions and purchases.

Consumptions and purchases never write inventory events by hand — they call
these functions, which emit / mutate / delete the paired INVENTORY event
(``decrement`` for consumption, ``increment`` for purchase) and guard against
negative stock. The event stream stays the single source of stock truth; these
helpers only keep it consistent inside the caller's transaction. The caller owns
commit/rollback.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import InsufficientStockError
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit

_CONSUMPTION_PAYLOAD = {"source": "material_consumption"}
_PURCHASE_PAYLOAD = {"source": "material_purchase"}


async def _lock_material(db: AsyncSession, asset_id: int) -> None:
    """Serialize concurrent stock mutations on one material asset."""
    await db.execute(select(Asset.id).where(Asset.id == asset_id).with_for_update())


async def _on_hand(db: AsyncSession, asset_id: int, unit: Unit) -> Decimal:
    """Replay INVENTORY events to the current on-hand balance for one unit."""
    stmt = (
        select(Event.adjustment, Event.quantity)
        .where(
            Event.asset_id == asset_id,
            Event.type == EventType.INVENTORY,
            Event.unit == unit,
        )
        .order_by(Event.occurred_at.asc(), Event.id.asc())
    )
    on_hand = Decimal(0)
    for adjustment, quantity in (await db.execute(stmt)).all():
        if adjustment is InventoryAdjustment.RESET:
            on_hand = Decimal(quantity)
        elif adjustment is InventoryAdjustment.INCREMENT:
            on_hand += Decimal(quantity)
        elif adjustment is InventoryAdjustment.DECREMENT:
            on_hand -= Decimal(quantity)
    return on_hand


async def _assert_non_negative(db: AsyncSession, asset_id: int, unit: Unit) -> None:
    if await _on_hand(db, asset_id, unit) < 0:
        raise InsufficientStockError(f"Operation would drive '{unit.value}' stock below zero")


async def emit_decrement(
    db: AsyncSession,
    *,
    material: Asset,
    unit: Unit,
    quantity: Decimal,
    occurred_at: datetime,
    created_by: int,
) -> Event:
    """Create the paired INVENTORY decrement event; reject if it oversells stock."""
    await _lock_material(db, material.id)
    event = Event(
        farm_id=material.farm_id,
        asset_id=material.id,
        type=EventType.INVENTORY,
        adjustment=InventoryAdjustment.DECREMENT,
        occurred_at=occurred_at,
        quantity=quantity,
        unit=unit,
        payload=dict(_CONSUMPTION_PAYLOAD),
        created_by=created_by,
    )
    db.add(event)
    await db.flush()
    await _assert_non_negative(db, material.id, unit)
    return event


async def reconcile_decrement(
    db: AsyncSession,
    *,
    material_id: int,
    event: Event,
    unit: Unit,
    quantity: Decimal,
    occurred_at: datetime,
) -> None:
    """Mutate the paired event in place; re-check every unit it touched."""
    await _lock_material(db, material_id)
    old_unit = event.unit
    event.unit = unit
    event.quantity = quantity
    event.occurred_at = occurred_at
    await db.flush()
    await _assert_non_negative(db, material_id, unit)
    if old_unit is not None and old_unit != unit:
        await _assert_non_negative(db, material_id, old_unit)


async def reverse_decrement(db: AsyncSession, *, event: Event) -> None:
    """Delete the paired event. Removing a decrement only raises stock."""
    await db.delete(event)
    await db.flush()


async def emit_increment(
    db: AsyncSession,
    *,
    material: Asset,
    unit: Unit,
    quantity: Decimal,
    occurred_at: datetime,
    created_by: int,
) -> Event:
    """Create the paired INVENTORY increment event. Increments only raise stock,
    so no guard or lock is needed at create time."""
    event = Event(
        farm_id=material.farm_id,
        asset_id=material.id,
        type=EventType.INVENTORY,
        adjustment=InventoryAdjustment.INCREMENT,
        occurred_at=occurred_at,
        quantity=quantity,
        unit=unit,
        payload=dict(_PURCHASE_PAYLOAD),
        created_by=created_by,
    )
    db.add(event)
    await db.flush()
    return event


async def reconcile_increment(
    db: AsyncSession,
    *,
    material_id: int,
    event: Event,
    unit: Unit,
    quantity: Decimal,
    occurred_at: datetime,
) -> None:
    """Mutate the paired event in place; reducing it can retroactively oversell."""
    await _lock_material(db, material_id)
    old_unit = event.unit
    event.unit = unit
    event.quantity = quantity
    event.occurred_at = occurred_at
    await db.flush()
    await _assert_non_negative(db, material_id, unit)
    if old_unit is not None and old_unit != unit:
        await _assert_non_negative(db, material_id, old_unit)


async def reverse_increment(db: AsyncSession, *, material_id: int, event: Event) -> None:
    """Delete the paired event; removing an increment can drive stock negative."""
    await _lock_material(db, material_id)
    unit = event.unit
    await db.delete(event)
    await db.flush()
    if unit is not None:
        await _assert_non_negative(db, material_id, unit)
