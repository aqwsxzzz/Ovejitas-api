"""add_individual_mortality_event_fk

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-17 12:00:00.000000+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "individual", sa.Column("mortality_event_id", sa.Integer(), nullable=True)
    )
    op.create_unique_constraint(
        op.f("uq_individual_mortality_event_id"), "individual", ["mortality_event_id"]
    )
    op.create_foreign_key(
        op.f("fk_individual_mortality_event_id_event"),
        "individual",
        "event",
        ["mortality_event_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_individual_mortality_event_id_event"), "individual", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("uq_individual_mortality_event_id"), "individual", type_="unique"
    )
    op.drop_column("individual", "mortality_event_id")
