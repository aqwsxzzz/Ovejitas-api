"""add_inventory_event_type

Revision ID: a1b2c3d4e5f6
Revises: 9f2c8e1d6a40
Create Date: 2026-05-11 12:00:00.000000+00:00

Adds the 'inventory' value to the event_type enum. Postgres requires new enum
values to be committed before they can be referenced in CHECK constraints or
partial-index predicates, so the table changes live in the next migration.
"""
from collections.abc import Sequence

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "9f2c8e1d6a40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'inventory'")


def downgrade() -> None:
    op.execute("ALTER TYPE event_type RENAME TO event_type_old")
    op.execute(
        "CREATE TYPE event_type AS ENUM "
        "('production', 'expense', 'income', 'observation', 'reproductive', "
        "'acquisition', 'mortality')"
    )
    op.execute(
        "ALTER TABLE event ALTER COLUMN type TYPE event_type "
        "USING type::text::event_type"
    )
    op.execute(
        "ALTER TABLE event_category ALTER COLUMN type TYPE event_type "
        "USING type::text::event_type"
    )
    op.execute("DROP TYPE event_type_old")
