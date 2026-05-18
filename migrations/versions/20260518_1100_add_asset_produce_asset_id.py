"""add_asset_produce_asset_id

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-05-18 11:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: str | None = "b8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("asset", sa.Column("produce_asset_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_asset_produce_asset_id"), "asset", ["produce_asset_id"])
    op.create_foreign_key(
        op.f("fk_asset_produce_asset_id_asset"),
        "asset",
        "asset",
        ["produce_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_asset_produce_asset_id_asset"), "asset", type_="foreignkey")
    op.drop_index(op.f("ix_asset_produce_asset_id"), table_name="asset")
    op.drop_column("asset", "produce_asset_id")
