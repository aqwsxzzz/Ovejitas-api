"""add_individual_birth_event_fk

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-05-18 10:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: str | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("individual", sa.Column("birth_event_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_individual_birth_event_id"), "individual", ["birth_event_id"])
    op.create_foreign_key(
        op.f("fk_individual_birth_event_id_event"),
        "individual",
        "event",
        ["birth_event_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_individual_birth_event_id_event"), "individual", type_="foreignkey")
    op.drop_index(op.f("ix_individual_birth_event_id"), table_name="individual")
    op.drop_column("individual", "birth_event_id")
