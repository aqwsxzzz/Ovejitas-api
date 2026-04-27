"""add_acquisition_and_mortality_event_types

Revision ID: 0d352869af19
Revises: 0a3a3ce9a25e
Create Date: 2026-04-27 16:05:00.000000+00:00

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0d352869af19"
down_revision: str | None = "0a3a3ce9a25e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'acquisition'")
    op.execute("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'mortality'")


def downgrade() -> None:
    # Postgres does not support removing enum values directly. Recreate the type
    # without the new values, repointing the column.
    op.execute("ALTER TYPE event_type RENAME TO event_type_old")
    op.execute(
        "CREATE TYPE event_type AS ENUM "
        "('production', 'expense', 'income', 'observation', 'reproductive')"
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
