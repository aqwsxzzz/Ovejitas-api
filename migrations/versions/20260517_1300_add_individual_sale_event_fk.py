"""add_individual_sale_event_fk

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-05-17 13:00:00.000000+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("individual", sa.Column("sale_event_id", sa.Integer(), nullable=True))
    op.create_unique_constraint(
        op.f("uq_individual_sale_event_id"), "individual", ["sale_event_id"]
    )
    op.create_foreign_key(
        op.f("fk_individual_sale_event_id_event"),
        "individual",
        "event",
        ["sale_event_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_individual_sale_event_id_event"), "individual", type_="foreignkey"
    )
    op.drop_constraint(op.f("uq_individual_sale_event_id"), "individual", type_="unique")
    op.drop_column("individual", "sale_event_id")
