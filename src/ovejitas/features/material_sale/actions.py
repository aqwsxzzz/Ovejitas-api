"""The material sale action — selling stock from a material asset (harvested
produce, surplus feed). One real-world act recorded as one transaction: an
INVENTORY decrement drawing the on-hand balance down + an INCOME event booking
the revenue, both tagged ``payload.source = "material_sale"`` (Philosophy 1).
The mirror image of material_purchase.

Create-only: no reconcile/reverse. The router calls ``create_material_sale``
directly.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.guards import validate_category
from ovejitas.features.event.inventory import emit_decrement, on_hand
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.farm.models import Farm
from ovejitas.features.material_consumption.guards import validate_unit_in_stock
from ovejitas.features.material_sale.guards import validate_sale_asset
from ovejitas.features.material_sale.schemas import MaterialSaleCreate, MaterialSaleRead

_SALE_SOURCE = "material_sale"


async def _farm_currency(db: AsyncSession, farm_id: int) -> str:
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise NotFoundError("Farm not found")
    return farm.default_currency


async def create_material_sale(
    db: AsyncSession, *, asset: Asset, user_id: int, data: MaterialSaleCreate
) -> MaterialSaleRead:
    """Decrement the material's stock and book the paired income, atomically."""
    validate_sale_asset(asset)
    await validate_unit_in_stock(db, asset.id, data.unit)
    await validate_category(db, asset.farm_id, EventType.INCOME, data.category_id)
    try:
        decrement = await emit_decrement(
            db,
            material=asset,
            unit=data.unit,
            quantity=data.quantity,
            occurred_at=data.occurred_at,
            created_by=user_id,
            source=_SALE_SOURCE,
        )
        currency = await _farm_currency(db, asset.farm_id)
        payload = {"source": _SALE_SOURCE}
        if data.buyer is not None:
            payload["buyer"] = data.buyer
        income = Event(
            farm_id=asset.farm_id,
            asset_id=asset.id,
            type=EventType.INCOME,
            occurred_at=data.occurred_at,
            amount=data.amount,
            currency=currency,
            category_id=data.category_id,
            notes=data.notes,
            payload=payload,
            created_by=user_id,
        )
        db.add(income)
        await db.flush()
        inventory_event_id, income_event_id = decrement.id, income.id
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    balance = await on_hand(db, asset.id, data.unit)
    return MaterialSaleRead(
        inventory_event_id=inventory_event_id,
        income_event_id=income_event_id,
        on_hand=balance,
    )
