"""The harvest action — collecting produce (eggs, milk, a crop yield) from an
animal or crop asset. One real-world act recorded as one transaction: a
PRODUCTION event on the source asset (per-source productivity) plus an
INVENTORY increment on the linked produce material asset (managed stock),
turning production into sellable inventory (Philosophy 1).

Create-only: no reconcile/reverse. The router calls ``create_harvest`` directly.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.guards import validate_category
from ovejitas.features.event.inventory import emit_increment, on_hand
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.harvest.guards import validate_harvest_source, validate_produce_unit
from ovejitas.features.harvest.schemas import HarvestCreate, HarvestRead

_HARVEST_SOURCE = "harvest"


async def create_harvest(
    db: AsyncSession, *, asset: Asset, user_id: int, data: HarvestCreate
) -> HarvestRead:
    """Emit the PRODUCTION event on ``asset`` and increment its linked produce
    asset's stock by the same quantity, atomically."""
    validate_harvest_source(asset)
    produce_asset = await db.get(Asset, asset.produce_asset_id)
    if produce_asset is None:
        raise NotFoundError("Linked produce asset not found")
    await validate_produce_unit(db, produce_asset.id, data.unit)
    await validate_category(db, asset.farm_id, EventType.PRODUCTION, data.category_id)
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
            payload={"source": _HARVEST_SOURCE},
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
