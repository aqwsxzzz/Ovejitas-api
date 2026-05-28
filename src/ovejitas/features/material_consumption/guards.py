"""Cross-entity validation for material consumptions.

``assert_consumer_rules`` is a pure check shared by the create schema and the
update service path; the rest hit the DB to confirm farm ownership, asset kind,
and that the material actually holds stock in the consumed unit.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.features.asset.models import Asset, AssetKind
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, Unit
from ovejitas.features.individual.models import Individual
from ovejitas.features.material_consumption.types import ConsumptionReason


def assert_consumer_rules(
    reason: ConsumptionReason,
    consumer_asset_id: int | None,
    individual_id: int | None,
) -> None:
    is_feeding = reason is ConsumptionReason.FEEDING
    if is_feeding and consumer_asset_id is None:
        raise ValidationError("feeding requires consumer_asset_id")
    if not is_feeding and consumer_asset_id is not None:
        raise ValidationError("waste/spoilage must not reference a consumer")
    if individual_id is not None and consumer_asset_id is None:
        raise ValidationError("individual_id requires consumer_asset_id")


async def _farm_asset(db: AsyncSession, farm_id: int, asset_id: int, label: str) -> Asset:
    stmt = select(Asset).where(Asset.id == asset_id, Asset.farm_id == farm_id)
    asset = (await db.execute(stmt)).scalar_one_or_none()
    if asset is None:
        raise NotFoundError(f"{label} not found")
    return asset


async def validate_material_asset(db: AsyncSession, farm_id: int, material_asset_id: int) -> Asset:
    asset = await _farm_asset(db, farm_id, material_asset_id, "Material asset")
    if asset.kind is not AssetKind.MATERIAL:
        raise ValidationError("material_asset_id must reference a material asset")
    return asset


async def validate_consumer(
    db: AsyncSession,
    farm_id: int,
    consumer_asset_id: int | None,
    individual_id: int | None,
) -> None:
    if consumer_asset_id is None:
        return
    asset = await _farm_asset(db, farm_id, consumer_asset_id, "Consumer asset")
    if asset.kind is not AssetKind.ANIMAL:
        raise ValidationError("consumer_asset_id must reference an animal asset")
    if individual_id is None:
        return
    stmt = select(Individual.id).where(
        Individual.id == individual_id,
        Individual.asset_id == consumer_asset_id,
    )
    if (await db.execute(stmt)).scalar_one_or_none() is None:
        raise ValidationError("individual_id does not belong to the consumer asset")


async def validate_unit_in_stock(db: AsyncSession, material_asset_id: int, unit: Unit) -> None:
    """Decision 3 — consumption unit must match a unit the material has stock in."""
    stmt = (
        select(Event.id)
        .where(
            Event.asset_id == material_asset_id,
            Event.type == EventType.INVENTORY,
            Event.unit == unit,
        )
        .limit(1)
    )
    if (await db.execute(stmt)).scalar_one_or_none() is None:
        raise ValidationError(f"Material has no recorded stock in unit '{unit.value}'")
