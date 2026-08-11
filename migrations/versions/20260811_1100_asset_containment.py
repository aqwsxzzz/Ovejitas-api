"""asset_containment

Containment becomes a relationship. `asset.location` was free text that happened,
or happened not, to be spelled like the name of a `location`-kind asset; nothing
kept the two in agreement, so "which animals are in this paddock" was a string
match that breaks on the first rename or typo. This is the same mistake the
product/pool split already fixed once — one real thing existing twice, with no
agreement between the copies — so the string does not survive alongside the link.

The backfill turns the text into the relationship rather than discarding it: for
each farm, every distinct non-empty `location` string becomes a `location` asset
(reusing one that already carries that name), and every asset that named it gets
linked. Junk strings become junk locations, which the farmer can now archive.

Downgrade copies the location's name back into the restored column, so the round
trip loses only the identity of locations the backfill had to create.

Revision ID: f6a7b8c9d0ec
Revises: e5f6a7b8c9db
Create Date: 2026-08-11 11:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0ec"
down_revision: str | None = "e5f6a7b8c9db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# One location asset per (farm, distinct non-empty location string) that does not
# already exist under that name. Trimmed, so " Galpon " and "Galpon" are one place.
_CREATE_LOCATIONS = """
INSERT INTO asset (farm_id, name, kind, created_at, updated_at)
SELECT DISTINCT a.farm_id, btrim(a.location), 'location'::asset_kind, now(), now()
FROM asset a
WHERE a.location IS NOT NULL
  AND btrim(a.location) <> ''
  AND NOT EXISTS (
      SELECT 1 FROM asset l
      WHERE l.farm_id = a.farm_id
        AND l.kind = 'location'::asset_kind
        AND l.name = btrim(a.location)
  )
"""

_LINK_ASSETS = """
UPDATE asset a
SET location_asset_id = l.id
FROM asset l
WHERE a.location IS NOT NULL
  AND btrim(a.location) <> ''
  AND l.farm_id = a.farm_id
  AND l.kind = 'location'::asset_kind
  AND l.name = btrim(a.location)
"""

_RESTORE_TEXT = """
UPDATE asset a
SET location = l.name
FROM asset l
WHERE a.location_asset_id = l.id
"""


def upgrade() -> None:
    op.add_column("asset", sa.Column("location_asset_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_asset_location_asset_id"), "asset", ["location_asset_id"])
    op.create_foreign_key(
        op.f("fk_asset_location_asset_id_asset"),
        "asset",
        "asset",
        ["location_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(_CREATE_LOCATIONS)
    op.execute(_LINK_ASSETS)
    op.drop_column("asset", "location")


def downgrade() -> None:
    op.add_column("asset", sa.Column("location", sa.String(length=255), nullable=True))
    op.execute(_RESTORE_TEXT)
    op.drop_constraint(op.f("fk_asset_location_asset_id_asset"), "asset", type_="foreignkey")
    op.drop_index(op.f("ix_asset_location_asset_id"), table_name="asset")
    op.drop_column("asset", "location_asset_id")
