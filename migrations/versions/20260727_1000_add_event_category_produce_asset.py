"""link a production category to the produce pool holding its stock

Revision ID: a1b2c3d4e5f7
Revises: f0a1b2c3d4e5
Create Date: 2026-07-27 10:00:00.000000+00:00

Schema half of "a product owns its pool". The column stays nullable because
non-production categories genuinely have none; "required for production" is
enforced at the API layer, matching how ``event_category.unit`` already works.

The UNIQUE constraint is the invariant the harvest depends on: one pool backs at
most one product, so the destination resolves from the product alone. It also
supplies the index for the foreign key.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f7"
down_revision: str | None = "f0a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "event_category",
        sa.Column("produce_asset_id", sa.Integer(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_event_category_produce_asset_id", "event_category", ["produce_asset_id"]
    )
    op.create_foreign_key(
        "fk_event_category_produce_asset_id_asset",
        "event_category",
        "asset",
        ["produce_asset_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_event_category_produce_asset_id_asset", "event_category", type_="foreignkey")
    op.drop_constraint("uq_event_category_produce_asset_id", "event_category", type_="unique")
    op.drop_column("event_category", "produce_asset_id")
