"""add_individual_acquisition_event_fks

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-17 11:00:00.000000+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "individual", sa.Column("acquisition_event_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "individual", sa.Column("acquisition_expense_event_id", sa.Integer(), nullable=True)
    )
    op.create_unique_constraint(
        op.f("uq_individual_acquisition_event_id"), "individual", ["acquisition_event_id"]
    )
    op.create_unique_constraint(
        op.f("uq_individual_acquisition_expense_event_id"),
        "individual",
        ["acquisition_expense_event_id"],
    )
    op.create_foreign_key(
        op.f("fk_individual_acquisition_event_id_event"),
        "individual",
        "event",
        ["acquisition_event_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        op.f("fk_individual_acquisition_expense_event_id_event"),
        "individual",
        "event",
        ["acquisition_expense_event_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_individual_acquisition_expense_event_id_event"),
        "individual",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_individual_acquisition_event_id_event"), "individual", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("uq_individual_acquisition_expense_event_id"), "individual", type_="unique"
    )
    op.drop_constraint(
        op.f("uq_individual_acquisition_event_id"), "individual", type_="unique"
    )
    op.drop_column("individual", "acquisition_expense_event_id")
    op.drop_column("individual", "acquisition_event_id")
