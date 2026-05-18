"""Cross-entity validation for the harvest action."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ValidationError
from ovejitas.features.asset.models import Asset, AssetKind
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, Unit


def validate_harvest_source(asset: Asset) -> None:
    """The source must be something that produces and must have a produce
    asset linked to receive the harvest."""
    if asset.kind not in (AssetKind.ANIMAL, AssetKind.CROP):
        raise ValidationError("Harvest requires an animal or crop asset")
    if asset.produce_asset_id is None:
        raise ValidationError("This asset has no produce asset linked")


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
