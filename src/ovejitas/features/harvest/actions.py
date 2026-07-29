"""The harvest action — collecting produce (eggs, milk, a crop yield) from an
animal or crop asset. One real-world act recorded as one transaction: a
PRODUCTION event on the source asset (per-source productivity), an INVENTORY
increment on the named produce material asset (managed stock), and the
PRODUCE_LOT row tying the two together so the pool remembers who contributed
what (Philosophy 1).

The request names only the product; its pool comes from
``event_category.produce_asset_id``, so the stock and the production event can
never be attributed to different products. ``asset.produce_asset_id`` survives
only as a UI default for which product a producer harvests by default.

Create-only: no reconcile/reverse. The router calls ``create_harvest`` directly.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.asset.models import Asset
from ovejitas.features.event.guards import validate_category
from ovejitas.features.event.inventory import emit_increment, on_hand
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.harvest.guards import (
    resolve_produce_asset,
    validate_harvest_source,
    validate_produce_unit,
)
from ovejitas.features.harvest.models import ProduceLot
from ovejitas.features.harvest.schemas import HarvestCreate, HarvestRead

_HARVEST_SOURCE = "harvest"


async def create_harvest(
    db: AsyncSession, *, asset: Asset, user_id: int, data: HarvestCreate
) -> HarvestRead:
    """Emit the PRODUCTION event on ``asset``, increment the named produce
    asset's stock by the same quantity, and record the lot — atomically."""
    validate_harvest_source(asset)
    # Destination first: it is the farm-scope boundary on the client-supplied
    # category id, and answers "not found" before anything else is revealed.
    produce_asset = await resolve_produce_asset(db, asset, data.category_id)
    await validate_category(db, asset.farm_id, EventType.PRODUCTION, data.category_id, data.unit)
    await validate_produce_unit(db, produce_asset.id, data.unit)
    try:
        production = Event(
            farm_id=asset.farm_id,
            asset_id=asset.id,
            type=EventType.PRODUCTION,
            occurred_at=data.occurred_at,
            quantity=data.quantity,
            unit=data.unit,
            category_id=data.category_id,
            notes=data.notes,
            payload={"source": _HARVEST_SOURCE, "produce_asset_id": produce_asset.id},
            created_by=user_id,
        )
        db.add(production)
        increment = await emit_increment(
            db,
            material=produce_asset,
            unit=data.unit,
            quantity=data.quantity,
            occurred_at=data.occurred_at,
            created_by=user_id,
            source=_HARVEST_SOURCE,
        )
        await db.flush()
        db.add(
            ProduceLot(
                farm_id=asset.farm_id,
                produce_asset_id=produce_asset.id,
                producer_asset_id=asset.id,
                production_event_id=production.id,
                inventory_event_id=increment.id,
                occurred_at=data.occurred_at,
                quantity=data.quantity,
                unit=data.unit,
                created_by=user_id,
            )
        )
        production_event_id, inventory_event_id = production.id, increment.id
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    produce_balance = await on_hand(db, produce_asset.id, data.unit)
    return HarvestRead(
        production_event_id=production_event_id,
        inventory_event_id=inventory_event_id,
        produce_balance=produce_balance,
    )
