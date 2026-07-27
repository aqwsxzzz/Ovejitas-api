"""The lifecycle of the produce pool backing a product.

Pools are never authored by hand — ``POST /assets`` rejects ``kind=produce``.
A production ``event_category`` provisions its own pool at creation time and
retires it on delete, so the farmer types "Huevos de gallina" once instead of
creating a category and a look-alike asset that nothing kept in agreement.

Both functions work inside the caller's transaction without committing: the
category and its pool must land together or not at all.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ValidationError
from ovejitas.features.asset.models import Asset, AssetKind
from ovejitas.features.event.balance import asset_has_events


def build_produce_pool(db: AsyncSession, *, farm_id: int, name: str) -> Asset:
    """Add the produce asset backing a product to the session and return it."""
    pool = Asset(farm_id=farm_id, name=name, kind=AssetKind.PRODUCE)
    db.add(pool)
    return pool


async def retire_produce_pool(db: AsyncSession, pool_id: int) -> None:
    """Delete a product's pool, refusing once it carries history.

    A pool with events has recorded stock — deleting it would cascade those
    inventory events away, so the product itself becomes undeletable instead.
    Callers must drop their reference to the pool before this runs, or the
    RESTRICT on ``event_category.produce_asset_id`` blocks the delete.
    """
    pool = await db.get(Asset, pool_id)
    if pool is None:
        return
    if await asset_has_events(db, pool_id):
        raise ValidationError(
            "Cannot delete a product whose produce pool already has recorded stock"
        )
    await db.delete(pool)
