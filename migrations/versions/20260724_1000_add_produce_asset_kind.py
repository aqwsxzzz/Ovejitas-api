"""add produce asset kind

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-07-24 10:00:00.000000+00:00

Adds the 'produce' value to the asset_kind enum, splitting farm output you
harvest into and sell (eggs, milk) out of the consumable-input 'material' kind.
Postgres requires a new enum value to be committed before rows can be set to it,
so the data backfill lives in the next migration (env.py runs each migration in
its own transaction).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e9f0a1b2c3d4"
down_revision: str | None = "d8e9f0a1b2c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE asset_kind ADD VALUE IF NOT EXISTS 'produce'")


def downgrade() -> None:
    # Recreate the enum without 'produce'. The backfill migration (applied first
    # on downgrade) has already moved every 'produce' row back to 'material', so
    # the USING cast below cannot hit an orphaned value.
    op.execute("ALTER TYPE asset_kind RENAME TO asset_kind_old")
    op.execute(
        "CREATE TYPE asset_kind AS ENUM "
        "('animal', 'crop', 'equipment', 'material', 'location')"
    )
    op.execute(
        "ALTER TABLE asset ALTER COLUMN kind TYPE asset_kind "
        "USING kind::text::asset_kind"
    )
    op.execute("DROP TYPE asset_kind_old")
