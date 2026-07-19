"""add asset_production_target table

Revision ID: e1f2a3b4c5d6
Revises: d7e8f9a0b1c2
Create Date: 2026-07-01 14:00:00.000000+00:00

A per-asset, per-product expected production rate. The product is a production
event_category; ``basis`` selects how the report scales the rate. Effective-dated
so a changed rate is a new row, keeping historical reports truthful.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: str | None = "d7e8f9a0b1c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BASIS = ("per_head_continuous", "per_event", "total")
_PERIOD = ("day", "year")


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")
    op.execute("CREATE TYPE production_basis AS ENUM (" + ", ".join(f"'{v}'" for v in _BASIS) + ")")
    op.execute("CREATE TYPE target_period AS ENUM (" + ", ".join(f"'{v}'" for v in _PERIOD) + ")")
    op.create_table(
        "asset_production_target",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "farm_id",
            sa.Integer(),
            sa.ForeignKey("farm.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("asset.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("event_category.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "basis",
            postgresql.ENUM(*_BASIS, name="production_basis", create_type=False),
            nullable=False,
        ),
        sa.Column("expected_rate", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "period",
            postgresql.ENUM(*_PERIOD, name="target_period", create_type=False),
            nullable=True,
        ),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.UniqueConstraint(
            "asset_id", "category_id", "effective_from", name="uq_target_asset_category_from"
        ),
        sa.CheckConstraint("expected_rate >= 0", name="ck_target_rate_non_negative"),
        sa.CheckConstraint(
            "(basis = 'per_head_continuous') = (period IS NOT NULL)",
            name="ck_target_period_for_continuous",
        ),
    )
    op.create_index("ix_target_farm", "asset_production_target", ["farm_id"])
    op.create_index("ix_target_category", "asset_production_target", ["category_id"])


def downgrade() -> None:
    op.drop_table("asset_production_target")
    op.execute("DROP TYPE target_period")
    op.execute("DROP TYPE production_basis")
