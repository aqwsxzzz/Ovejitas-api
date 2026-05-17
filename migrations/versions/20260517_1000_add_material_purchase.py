"""add_material_purchase

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-17 10:00:00.000000+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UNIT_VALUES = ("g", "kg", "lb", "t", "ml", "l", "gal", "unit", "dozen", "head")


def upgrade() -> None:
    op.create_table(
        "material_purchase",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("material_asset_id", sa.Integer(), nullable=False),
        sa.Column("inventory_event_id", sa.Integer(), nullable=False),
        sa.Column("expense_event_id", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.Column("unit", postgresql.ENUM(*_UNIT_VALUES, name="unit", create_type=False), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("supplier", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_material_purchase_quantity_positive")),
        sa.CheckConstraint("amount > 0", name=op.f("ck_material_purchase_amount_positive")),
        sa.ForeignKeyConstraint(
            ["farm_id"], ["farm.id"],
            name=op.f("fk_material_purchase_farm_id_farm"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["material_asset_id"], ["asset.id"],
            name=op.f("fk_material_purchase_material_asset_id_asset"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_event_id"], ["event.id"],
            name=op.f("fk_material_purchase_inventory_event_id_event"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["expense_event_id"], ["event.id"],
            name=op.f("fk_material_purchase_expense_event_id_event"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["user.id"],
            name=op.f("fk_material_purchase_created_by_user"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_material_purchase")),
        sa.UniqueConstraint(
            "inventory_event_id", name=op.f("uq_material_purchase_inventory_event_id")
        ),
        sa.UniqueConstraint(
            "expense_event_id", name=op.f("uq_material_purchase_expense_event_id")
        ),
    )
    op.create_index(
        "ix_material_purchase_farm_occurred",
        "material_purchase", ["farm_id", "occurred_at"], unique=False,
    )
    op.create_index(
        "ix_material_purchase_material_occurred",
        "material_purchase", ["farm_id", "material_asset_id", "occurred_at"], unique=False,
    )
    op.create_index(
        "uq_material_purchase_farm_idempotency_key",
        "material_purchase", ["farm_id", "idempotency_key"],
        unique=True, postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_material_purchase_farm_idempotency_key", table_name="material_purchase",
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.drop_index("ix_material_purchase_material_occurred", table_name="material_purchase")
    op.drop_index("ix_material_purchase_farm_occurred", table_name="material_purchase")
    op.drop_table("material_purchase")
