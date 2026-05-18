from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ValidationError
from ovejitas.features.asset.models import Asset, AssetKind, AssetMode
from ovejitas.features.event.types import EventType
from ovejitas.features.event_category.models import EventCategory
from ovejitas.features.individual.models import Individual


def _asset_tracks_inventory(asset: Asset) -> bool:
    """Inventory events are valid for a material asset, or for a flock — an
    animal asset counted in aggregate."""
    if asset.kind is AssetKind.MATERIAL:
        return True
    return asset.kind is AssetKind.ANIMAL and asset.mode is AssetMode.AGGREGATED


async def validate_type_against_asset(event_type: EventType, asset: Asset) -> None:
    if event_type is EventType.REPRODUCTIVE and asset.kind is not AssetKind.ANIMAL:
        raise ValidationError("Reproductive events require an animal asset")
    if event_type is EventType.INVENTORY and not _asset_tracks_inventory(asset):
        raise ValidationError(
            "Inventory events require a material asset or an aggregated animal asset"
        )


async def validate_individual(
    db: AsyncSession,
    asset: Asset,
    individual_id: int | None,
) -> None:
    if individual_id is None:
        return
    if asset.mode is not AssetMode.INDIVIDUAL:
        raise ValidationError("Cannot attach an individual to an aggregated asset")
    stmt = select(Individual).where(
        Individual.id == individual_id,
        Individual.asset_id == asset.id,
    )
    if (await db.execute(stmt)).scalar_one_or_none() is None:
        raise ValidationError("Individual does not belong to this asset")


async def validate_category(
    db: AsyncSession,
    farm_id: int,
    event_type: EventType,
    category_id: int | None,
) -> None:
    if category_id is None:
        return
    stmt = select(EventCategory).where(
        EventCategory.id == category_id,
        EventCategory.farm_id == farm_id,
    )
    category = (await db.execute(stmt)).scalar_one_or_none()
    if category is None:
        raise ValidationError("Category not found in this farm")
    if category.type is not event_type:
        raise ValidationError("Category type does not match event type")
