"""typed_event_unit

Revision ID: 9f2c8e1d6a40
Revises: 7c1a2b3d4e5f
Create Date: 2026-04-30 15:00:00.000000+00:00

"""
from collections.abc import Sequence

from alembic import op

revision: str = "9f2c8e1d6a40"
down_revision: str | None = "7c1a2b3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_UNIT_VALUES = ("g", "kg", "lb", "t", "ml", "l", "gal", "unit", "dozen", "head")


def upgrade() -> None:
    op.execute("ALTER TABLE event DROP COLUMN unit")
    op.execute(
        "CREATE TYPE unit AS ENUM ("
        + ", ".join(f"'{v}'" for v in _UNIT_VALUES)
        + ")"
    )
    op.execute("ALTER TABLE event ADD COLUMN unit unit")


def downgrade() -> None:
    op.execute("ALTER TABLE event DROP COLUMN unit")
    op.execute("DROP TYPE unit")
    op.execute("ALTER TABLE event ADD COLUMN unit VARCHAR(32)")
