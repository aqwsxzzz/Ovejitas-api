from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Identity, Index, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin


class AssetKind(StrEnum):
    ANIMAL = "animal"
    CROP = "crop"
    EQUIPMENT = "equipment"
    MATERIAL = "material"
    PRODUCE = "produce"
    LOCATION = "location"


# Asset kinds that carry an inventory balance: they bear INVENTORY events and are
# sold via the material-sale action. MATERIAL is consumable input you buy;
# PRODUCE is farm output you harvest into and sell. Reference this set, never the
# bare values, so a future stock-bearing kind slots in here exactly once.
INVENTORY_KINDS = frozenset({AssetKind.MATERIAL, AssetKind.PRODUCE})


class AssetMode(StrEnum):
    AGGREGATED = "aggregated"
    INDIVIDUAL = "individual"


class Asset(Base, TimestampMixin):
    __tablename__ = "asset"
    __table_args__ = (
        CheckConstraint(
            "gestation_days IS NULL OR gestation_days BETWEEN 20 AND 400",
            name="gestation_days_sane",
        ),
        Index("ix_asset_farm_kind", "farm_id", "kind"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farm.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[AssetKind] = mapped_column(
        SQLEnum(AssetKind, name="asset_kind", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    # Tracking mode is only meaningful for animals (the head-by-head vs lump
    # distinction backing the individual feature). Material/equipment/location
    # — and crops — carry no individuals, so mode is null for them.
    mode: Mapped[AssetMode | None] = mapped_column(
        SQLEnum(AssetMode, name="asset_mode", values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # The produce material asset this asset harvests into (e.g. a hen flock ->
    # an "Eggs" asset). Set on animal/crop assets; null until linked. SET NULL
    # on delete so a deleted produce asset just unlinks rather than dangling.
    produce_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("asset.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # How long this animal carries a pregnancy, in days — the farm's own number,
    # not a species lookup. Null means the farmer hasn't told us, and a due date
    # is simply never derived from it. Only animals gestate; every other kind
    # leaves it null (enforced in the service alongside the mode rule).
    gestation_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # When the farmer took this asset out of circulation — sold the flock, pulled
    # the field, retired the tractor. An asset with events cannot change kind or
    # mode and cannot be deleted once it has harvests, so without this there is
    # no supported way to stop it appearing in every picker forever. Archiving
    # destroys nothing: history, harvests and stock all stay exactly as recorded.
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
