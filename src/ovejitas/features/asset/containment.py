"""Where an asset is — the rules behind ``asset.location_asset_id``.

Containment used to be a free-text string that happened, or happened not, to be
spelled like the name of a ``location`` asset. Nothing kept the two in
agreement, so "which animals are in this paddock" could only be answered by a
string match that breaks on the first rename or typo. It is a foreign key now.

Two rules, kept apart because they apply at different moments: a target must be
a real location in the same farm (checked on create and on update), and a move
must not close a loop (only possible on update, since a brand-new asset is not
yet anybody's container).

Containment nests — a pen sits in a paddock sits in a field — but reads match on
the link itself, not on descendants. Nothing needs a rollup yet, and inventing
one now would be guessing at the shape of a report nobody has asked for.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.features.asset.models import Asset, AssetKind

# A loop needs at least two links, so any real chain is short. This only bounds
# a walk over data that a pre-existing cycle could otherwise make endless.
_MAX_DEPTH = 64


async def assert_valid_location(db: AsyncSession, *, farm_id: int, location_asset_id: int) -> None:
    """The target must be a location asset belonging to this farm."""
    stmt = select(Asset.kind).where(Asset.id == location_asset_id, Asset.farm_id == farm_id)
    kind = (await db.execute(stmt)).scalar_one_or_none()
    if kind is None:
        raise NotFoundError("Location asset not found")
    if kind is not AssetKind.LOCATION:
        raise ValidationError("location_asset_id must reference a location asset")


async def assert_no_location_cycle(
    db: AsyncSession, *, asset_id: int, location_asset_id: int
) -> None:
    """Refuse a move that would put an asset inside itself, directly or via a chain.

    Walks up from the proposed container. Reaching the asset being moved means
    the link closes a loop — a paddock inside the pen it contains — which would
    make any future "what is in here" read non-terminating.
    """
    current: int | None = location_asset_id
    for _ in range(_MAX_DEPTH):
        if current is None:
            return
        if current == asset_id:
            raise ValidationError("An asset cannot be contained by itself")
        stmt = select(Asset.location_asset_id).where(Asset.id == current)
        current = (await db.execute(stmt)).scalar_one_or_none()
    raise ValidationError("Location chain is too deep to verify")
