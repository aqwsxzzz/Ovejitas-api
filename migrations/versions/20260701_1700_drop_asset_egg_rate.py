"""drop asset.expected_eggs_per_head_per_day

Revision ID: a3c4d5e6f7a8
Revises: f2a3b4c5d6e7
Create Date: 2026-07-01 17:00:00.000000+00:00

The egg laying-rate has been migrated into asset_production_target rows (see the
backfill migration), so the egg-specific column is retired. Run only after the
backfill. Downgrade re-adds the (empty) column; the values are not restored.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3c4d5e6f7a8"
down_revision: str | None = "f2a3b4c5d6e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_asset_expected_eggs_non_negative", "asset", type_="check")
    op.drop_column("asset", "expected_eggs_per_head_per_day")


def downgrade() -> None:
    op.add_column(
        "asset",
        sa.Column("expected_eggs_per_head_per_day", sa.Numeric(6, 3), nullable=True),
    )
    op.create_check_constraint(
        "ck_asset_expected_eggs_non_negative",
        "asset",
        "expected_eggs_per_head_per_day >= 0",
    )
