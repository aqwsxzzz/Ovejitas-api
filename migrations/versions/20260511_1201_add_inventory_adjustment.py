"""add_inventory_adjustment

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-11 12:01:00.000000+00:00

"""
from collections.abc import Sequence

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE inventory_adjustment AS ENUM ('increment', 'decrement', 'reset')"
    )
    op.execute("ALTER TABLE event ADD COLUMN adjustment inventory_adjustment")
    op.execute(
        "ALTER TABLE event ADD CONSTRAINT inventory_requires_adjustment "
        "CHECK ((type = 'inventory') = (adjustment IS NOT NULL))"
    )
    op.execute(
        "CREATE INDEX ix_event_inventory_asset_occurred "
        "ON event (asset_id, occurred_at) WHERE type = 'inventory'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_event_inventory_asset_occurred")
    op.execute("ALTER TABLE event DROP CONSTRAINT IF EXISTS inventory_requires_adjustment")
    op.execute("DELETE FROM event WHERE type = 'inventory'")
    op.execute("ALTER TABLE event DROP COLUMN adjustment")
    op.execute("DROP TYPE inventory_adjustment")
