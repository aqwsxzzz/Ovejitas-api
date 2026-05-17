"""Cross-entity validation for material purchases.

Confirms farm ownership and asset kind, and that the purchased unit is
consistent with how the material is already tracked.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.features.asset.models import Asset, AssetKind
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, Unit


async def validate_material_asset(db: AsyncSession, farm_id: int, material_asset_id: int) -> Asset:
    stmt = select(Asset).where(Asset.id == material_asset_id, Asset.farm_id == farm_id)
    asset = (await db.execute(stmt)).scalar_one_or_none()
    if asset is None:
        raise NotFoundError("Material asset not found")
    if asset.kind is not AssetKind.MATERIAL:
        raise ValidationError("material_asset_id must reference a material asset")
    return asset


async def validate_purchase_unit(db: AsyncSession, material_asset_id: int, unit: Unit) -> None:
    """Purchase unit must match the material's existing inventory unit(s); any
    unit is allowed only when the material has no inventory history yet."""
    stmt = (
        select(Event.unit)
        .where(Event.asset_id == material_asset_id, Event.type == EventType.INVENTORY)
        .distinct()
    )
    units = {u for u in (await db.execute(stmt)).scalars().all() if u is not None}
    if units and unit not in units:
        existing = ", ".join(sorted(u.value for u in units))
        raise ValidationError(
            f"Material is tracked in [{existing}]; cannot purchase in '{unit.value}'"
        )
