"""add_produce_lot

Records which producer contributed each harvest into a shared produce asset, so
per-producer revenue can be derived by a FIFO draw over the pool.

Create only — no backfill. Existing harvests emitted two unlinked events with no
record of the destination, so their contributions are not recoverable; test data
is re-seeded instead.

Revision ID: c7d8e9f0a1b2
Revises: b1c2d3e4f5a6
Create Date: 2026-07-22 15:00:00.000000+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c7d8e9f0a1b2"
down_revision: str | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UNIT_VALUES = ("g", "kg", "lb", "t", "ml", "l", "gal", "unit", "dozen", "head")


def upgrade() -> None:
    op.create_table(
        "produce_lot",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("produce_asset_id", sa.Integer(), nullable=False),
        sa.Column("producer_asset_id", sa.Integer(), nullable=False),
        sa.Column("production_event_id", sa.Integer(), nullable=False),
        sa.Column("inventory_event_id", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.Column(
            "unit",
            postgresql.ENUM(*_UNIT_VALUES, name="unit", create_type=False),
            nullable=False,
        ),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_produce_lot_quantity_positive")),
        sa.CheckConstraint(
            "produce_asset_id <> producer_asset_id",
            name=op.f("ck_produce_lot_producer_is_not_pool"),
        ),
        sa.ForeignKeyConstraint(
            ["farm_id"], ["farm.id"],
            name=op.f("fk_produce_lot_farm_id_farm"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["produce_asset_id"], ["asset.id"],
            name=op.f("fk_produce_lot_produce_asset_id_asset"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["producer_asset_id"], ["asset.id"],
            name=op.f("fk_produce_lot_producer_asset_id_asset"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["production_event_id"], ["event.id"],
            name=op.f("fk_produce_lot_production_event_id_event"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_event_id"], ["event.id"],
            name=op.f("fk_produce_lot_inventory_event_id_event"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["user.id"],
            name=op.f("fk_produce_lot_created_by_user"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_produce_lot")),
        sa.UniqueConstraint("production_event_id", name=op.f("uq_produce_lot_production_event_id")),
        sa.UniqueConstraint("inventory_event_id", name=op.f("uq_produce_lot_inventory_event_id")),
    )
    # The FIFO scan: equality on the pool, then oldest-first, id breaking ties.
    op.create_index(
        "ix_produce_lot_pool_occurred",
        "produce_lot", ["produce_asset_id", "occurred_at", "id"], unique=False,
    )
    op.create_index(
        "ix_produce_lot_producer_occurred",
        "produce_lot", ["producer_asset_id", "occurred_at"], unique=False,
    )
    op.create_index(
        "ix_produce_lot_farm_occurred",
        "produce_lot", ["farm_id", "occurred_at"], unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_produce_lot_farm_occurred", table_name="produce_lot")
    op.drop_index("ix_produce_lot_producer_occurred", table_name="produce_lot")
    op.drop_index("ix_produce_lot_pool_occurred", table_name="produce_lot")
    op.drop_table("produce_lot")
