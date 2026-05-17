"""add_material_consumption

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-16 10:00:00.000000+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UNIT_VALUES = ("g", "kg", "lb", "t", "ml", "l", "gal", "unit", "dozen", "head")
_REASON_VALUES = ("feeding", "waste", "spoilage")


def upgrade() -> None:
    op.execute(
        "CREATE TYPE consumption_reason AS ENUM ("
        + ", ".join(f"'{v}'" for v in _REASON_VALUES)
        + ")"
    )
    op.create_table(
        "material_consumption",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("material_asset_id", sa.Integer(), nullable=False),
        sa.Column("consumer_asset_id", sa.Integer(), nullable=True),
        sa.Column("individual_id", sa.Integer(), nullable=True),
        sa.Column("inventory_event_id", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.Column("unit", postgresql.ENUM(*_UNIT_VALUES, name="unit", create_type=False), nullable=False),
        sa.Column(
            "reason",
            postgresql.ENUM(*_REASON_VALUES, name="consumption_reason", create_type=False),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_material_consumption_quantity_positive")),
        sa.CheckConstraint(
            "(reason = 'feeding') = (consumer_asset_id IS NOT NULL)",
            name=op.f("ck_material_consumption_feeding_requires_consumer"),
        ),
        sa.CheckConstraint(
            "individual_id IS NULL OR consumer_asset_id IS NOT NULL",
            name=op.f("ck_material_consumption_individual_requires_consumer"),
        ),
        sa.ForeignKeyConstraint(
            ["farm_id"], ["farm.id"],
            name=op.f("fk_material_consumption_farm_id_farm"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["material_asset_id"], ["asset.id"],
            name=op.f("fk_material_consumption_material_asset_id_asset"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["consumer_asset_id"], ["asset.id"],
            name=op.f("fk_material_consumption_consumer_asset_id_asset"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["individual_id"], ["individual.id"],
            name=op.f("fk_material_consumption_individual_id_individual"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_event_id"], ["event.id"],
            name=op.f("fk_material_consumption_inventory_event_id_event"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["user.id"],
            name=op.f("fk_material_consumption_created_by_user"), ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_material_consumption")),
        sa.UniqueConstraint(
            "inventory_event_id", name=op.f("uq_material_consumption_inventory_event_id")
        ),
    )
    op.create_index(
        "ix_material_consumption_farm_occurred",
        "material_consumption", ["farm_id", "occurred_at"], unique=False,
    )
    op.create_index(
        "ix_material_consumption_material_occurred",
        "material_consumption", ["farm_id", "material_asset_id", "occurred_at"], unique=False,
    )
    op.create_index(
        "ix_material_consumption_consumer_occurred",
        "material_consumption", ["farm_id", "consumer_asset_id", "occurred_at"],
        unique=False, postgresql_where=sa.text("consumer_asset_id IS NOT NULL"),
    )
    op.create_index(
        "uq_material_consumption_farm_idempotency_key",
        "material_consumption", ["farm_id", "idempotency_key"],
        unique=True, postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_material_consumption_farm_idempotency_key", table_name="material_consumption",
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.drop_index(
        "ix_material_consumption_consumer_occurred", table_name="material_consumption",
        postgresql_where=sa.text("consumer_asset_id IS NOT NULL"),
    )
    op.drop_index(
        "ix_material_consumption_material_occurred", table_name="material_consumption"
    )
    op.drop_index("ix_material_consumption_farm_occurred", table_name="material_consumption")
    op.drop_table("material_consumption")
    op.execute("DROP TYPE consumption_reason")
