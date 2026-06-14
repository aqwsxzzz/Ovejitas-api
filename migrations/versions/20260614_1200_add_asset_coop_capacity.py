"""add asset expected_eggs_per_head_per_day (laying rate)

Revision ID: c5d6e7f8a9b0
Revises: a3b4c5d6e7f8
Create Date: 2026-06-14 12:00:00.000000+00:00

Headcount is intentionally NOT stored — it is derived live from the flock's
HEAD inventory events. Only the expected laying rate needs persisting.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5d6e7f8a9b0"
down_revision: str | None = "a3b4c5d6e7f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")
    # Nullable, no default → instant add (no table rewrite, no backfill).
    op.add_column(
        "asset",
        sa.Column("expected_eggs_per_head_per_day", sa.Numeric(6, 3), nullable=True),
    )
    op.create_check_constraint(
        "ck_asset_expected_eggs_non_negative",
        "asset",
        "expected_eggs_per_head_per_day >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_asset_expected_eggs_non_negative", "asset", type_="check")
    op.drop_column("asset", "expected_eggs_per_head_per_day")
