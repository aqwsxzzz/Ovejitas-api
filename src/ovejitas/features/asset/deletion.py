"""What blocks an asset's hard delete, and how to say so.

Six foreign keys point at ``asset.id`` with ``ON DELETE RESTRICT``, and one more
path runs through the individuals an asset owns: a ``pregnancy`` holds its
individual with RESTRICT, so the CASCADE that clears an asset's individuals is
refused. The database is right to refuse — a produce lot is a recorded harvest
feeding the productivity report and the pool's stock balance, not incidental
plumbing. So the refusal is named rather than left to escape as a 500, and
archival is what takes a retired asset out of circulation instead.

One declaration list backs both readers — the guard in ``AssetService.delete``
and the ``deletable`` flag on ``AssetRead`` — so the flag and the outcome cannot
disagree. Every clause is an ``EXISTS`` correlated to whichever asset id it is
handed: a literal for the single-asset guard, ``Asset.id`` for the bulk flag.

Not listed here: events, individuals and production targets, which cascade away
cleanly with the asset, and ``asset.produce_asset_id``, which is SET NULL.
"""

from collections.abc import Sequence

from sqlalchemy import ColumnElement, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from ovejitas.features.asset.models import Asset
from ovejitas.features.event_category.models import EventCategory
from ovejitas.features.harvest.models import ProduceLot
from ovejitas.features.individual.models import Individual
from ovejitas.features.material_consumption.models import MaterialConsumption
from ovejitas.features.material_purchase.models import MaterialPurchase
from ovejitas.features.pregnancy.models import Pregnancy

AssetId = ColumnElement[int] | InstrumentedAttribute[int] | int


def _blockers(asset_id: AssetId) -> list[tuple[str, ColumnElement[bool]]]:
    """Every reference that would refuse this asset's delete, with the record it
    names — ordered so the most specific relationship is reported first."""
    return [
        (
            "Cannot delete an asset with recorded harvests",
            select(ProduceLot.id).where(ProduceLot.producer_asset_id == asset_id).exists(),
        ),
        (
            "Cannot delete a produce pool holding recorded harvests",
            select(ProduceLot.id).where(ProduceLot.produce_asset_id == asset_id).exists(),
        ),
        (
            "Cannot delete a produce pool that backs a production category",
            select(EventCategory.id).where(EventCategory.produce_asset_id == asset_id).exists(),
        ),
        (
            "Cannot delete an asset with recorded feed consumption",
            select(MaterialConsumption.id)
            .where(MaterialConsumption.consumer_asset_id == asset_id)
            .exists(),
        ),
        (
            "Cannot delete a material with recorded consumption",
            select(MaterialConsumption.id)
            .where(MaterialConsumption.material_asset_id == asset_id)
            .exists(),
        ),
        (
            "Cannot delete a material with recorded purchases",
            select(MaterialPurchase.id)
            .where(MaterialPurchase.material_asset_id == asset_id)
            .exists(),
        ),
        (
            "Cannot delete an asset whose individuals have recorded pregnancies",
            select(Pregnancy.id)
            .join(
                Individual,
                or_(
                    Individual.id == Pregnancy.individual_id,
                    Individual.id == Pregnancy.sire_individual_id,
                ),
            )
            .where(Individual.asset_id == asset_id)
            .exists(),
        ),
    ]


async def blocking_reason(db: AsyncSession, asset_id: int) -> str | None:
    """The message naming what blocks this asset's delete, or None if nothing does.

    All clauses are evaluated in one round trip; Postgres short-circuits each
    ``EXISTS`` on its first matching row.
    """
    blockers = _blockers(asset_id)
    stmt = select(*(clause for _, clause in blockers))
    flags = (await db.execute(stmt)).one()
    for (message, _), blocked in zip(blockers, flags, strict=True):
        if blocked:
            return message
    return None


async def deletable_map(db: AsyncSession, asset_ids: Sequence[int]) -> dict[int, bool]:
    """Which of these assets nothing blocks — one query for the whole page.

    The clauses correlate to ``Asset.id``, so a page of N assets costs a single
    statement rather than N reachability probes.
    """
    if not asset_ids:
        return {}
    blocked = or_(*(clause for _, clause in _blockers(Asset.id)))
    stmt = select(Asset.id, blocked).where(Asset.id.in_(asset_ids))
    rows = (await db.execute(stmt)).all()
    return {asset_id: not is_blocked for asset_id, is_blocked in rows}
