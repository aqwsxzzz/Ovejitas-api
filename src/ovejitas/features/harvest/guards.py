"""Cross-entity validation for the harvest action."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.features.asset.models import Asset, AssetKind
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, Unit
from ovejitas.features.event_category.models import EventCategory


def validate_harvest_source(asset: Asset) -> None:
    """The source must be something that produces. The destination is named on
    the request, not read from the asset, so no link is required here."""
    if asset.kind not in (AssetKind.ANIMAL, AssetKind.CROP):
        raise ValidationError("Harvest requires an animal or crop asset")


async def resolve_produce_asset(db: AsyncSession, source: Asset, category_id: int) -> Asset:
    """Load the pool backing the named product, refusing anything the caller must
    not reach through it.

    The category id is client-supplied, so this is the authorization boundary: a
    category in another farm is reported as not found rather than confirmed to
    exist. ``validate_category`` still checks the product's type and unit — this
    only resolves where its stock goes.
    """
    category = await db.get(EventCategory, category_id)
    if category is None or category.farm_id != source.farm_id:
        raise NotFoundError("Category not found in this farm")
    if category.type is not EventType.PRODUCTION:
        raise ValidationError("Harvest requires a production category")
    if category.produce_asset_id is None:
        raise ValidationError("This product has no produce pool to harvest into")
    produce_asset = await db.get(Asset, category.produce_asset_id)
    if produce_asset is None or produce_asset.kind is not AssetKind.PRODUCE:
        raise ValidationError("This product's produce pool is missing")
    if produce_asset.id == source.id:
        raise ValidationError("An asset cannot harvest into itself")
    return produce_asset


async def validate_produce_unit(db: AsyncSession, produce_asset_id: int, unit: Unit) -> None:
    """A produce asset holds stock in a single unit. The first harvest into an
    empty produce asset sets that unit; later harvests must match it."""
    stmt = (
        select(Event.unit)
        .where(
            Event.asset_id == produce_asset_id,
            Event.type == EventType.INVENTORY,
        )
        .limit(1)
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing is not None and existing != unit:
        raise ValidationError(
            f"Produce asset already tracks stock in '{existing.value}' — harvest unit must match"
        )
