from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Identity, Index, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin


class AssetKind(StrEnum):
    ANIMAL = "animal"
    CROP = "crop"
    EQUIPMENT = "equipment"
    MATERIAL = "material"
    LOCATION = "location"


class AssetMode(StrEnum):
    AGGREGATED = "aggregated"
    INDIVIDUAL = "individual"


class Asset(Base, TimestampMixin):
    __tablename__ = "asset"
    __table_args__ = (
        Index("ix_asset_farm_kind", "farm_id", "kind"),
        CheckConstraint(
            "expected_eggs_per_head_per_day >= 0",
            name="ck_asset_expected_eggs_non_negative",
        ),
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
    mode: Mapped[AssetMode] = mapped_column(
        SQLEnum(AssetMode, name="asset_mode", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
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
    # Expected laying rate (eggs per head per day, e.g. 0.8) for the
    # coop-productivity report — NUMERIC, never float. Null until configured.
    # Headcount is NOT stored here: it is the live HEAD on-hand derived from the
    # flock acquisition/sale/mortality events (see features/flock).
    expected_eggs_per_head_per_day: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 3), nullable=True
    )
