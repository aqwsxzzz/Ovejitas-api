"""backfill produce pools into the produce asset kind

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-07-24 10:10:00.000000+00:00

Reclassifies existing produce pools from 'material' to the new 'produce' kind,
using the two unambiguous signals for "this material asset is a produce pool":

1. It has received a harvest lot (``produce_lot.produce_asset_id``), or
2. A producer asset points at it as its produce target
   (``asset.produce_asset_id``).

Data-only. Known bounded gap: a pool harvested into before ``produce_lot``
existed (2026-07-22) AND never linked from a producer is not caught here and
must be reclassified by hand. Downgrade moves every 'produce' row back to
'material' so the enum can be recreated without the value.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f0a1b2c3d4e5"
down_revision: str | None = "e9f0a1b2c3d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE asset SET kind = 'produce'
        WHERE kind = 'material'
          AND (
            id IN (SELECT produce_asset_id FROM produce_lot)
            OR id IN (
              SELECT produce_asset_id FROM asset
              WHERE produce_asset_id IS NOT NULL
            )
          )
        """
    )


def downgrade() -> None:
    op.execute("UPDATE asset SET kind = 'material' WHERE kind = 'produce'")
