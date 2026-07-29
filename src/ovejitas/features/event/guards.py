from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import ValidationError
from ovejitas.features.asset.models import INVENTORY_KINDS, Asset, AssetKind, AssetMode
from ovejitas.features.event.types import EventType, Unit
from ovejitas.features.event_category.models import EventCategory
from ovejitas.features.individual.models import Individual

# Units that measure the same physical quantity — a production event may be logged
# in any unit within its category's family (e.g. eggs in unit or dozen). Numeric
# conversion between them is the report's concern, not this guard's.
_UNIT_FAMILIES: tuple[frozenset[Unit], ...] = (
    frozenset({Unit.UNIT, Unit.DOZEN}),
    frozenset({Unit.G, Unit.KG, Unit.LB, Unit.T}),
    frozenset({Unit.ML, Unit.L, Unit.GAL}),
    frozenset({Unit.HEAD}),
)


def _same_family(a: Unit, b: Unit) -> bool:
    return any(a in family and b in family for family in _UNIT_FAMILIES)


def _asset_tracks_inventory(asset: Asset) -> bool:
    """Inventory events are valid for a stock-bearing asset (material or produce),
    or for a flock — an animal asset counted in aggregate."""
    if asset.kind in INVENTORY_KINDS:
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
    unit: Unit | None = None,
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
    # For production, the event's unit must be compatible with the product's unit
    # (same measurement family). Legacy categories without a unit are skipped —
    # "unit required" is enforced at category creation, going forward.
    if (
        event_type is EventType.PRODUCTION
        and category.unit is not None
        and unit is not None
        and not _same_family(unit, category.unit)
    ):
        raise ValidationError(
            f"Event unit '{unit.value}' is not compatible with "
            f"category unit '{category.unit.value}'"
        )


_TYPE_SPECIFIC_FIELDS: dict[EventType, frozenset[str]] = {
    EventType.PRODUCTION: frozenset({"quantity", "unit"}),
    EventType.OBSERVATION: frozenset({"quantity", "unit"}),
    EventType.EXPENSE: frozenset({"amount"}),
    EventType.INCOME: frozenset({"amount"}),
    EventType.INVENTORY: frozenset({"quantity", "unit", "adjustment"}),
    EventType.REPRODUCTIVE: frozenset(),
}
_COMMON_EVENT_FIELDS: frozenset[str] = frozenset(
    {"occurred_at", "individual_id", "category_id", "notes", "payload"}
)


def assert_fields_valid_for_type(event_type: EventType, fields: Iterable[str]) -> None:
    """Reject EventUpdate fields that make no sense for the event's type — e.g.
    an ``amount`` on a production event or an ``adjustment`` on an observation."""
    allowed = _COMMON_EVENT_FIELDS | _TYPE_SPECIFIC_FIELDS.get(event_type, frozenset())
    invalid = sorted(set(fields) - allowed)
    if invalid:
        raise ValidationError(f"Fields {invalid} are not valid for a {event_type.value} event")
