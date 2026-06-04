"""add farm_member.invited_by

Revision ID: a3b4c5d6e7f8
Revises: 723c6bf46fa3
Create Date: 2026-06-03 10:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3b4c5d6e7f8"
down_revision: str | None = "723c6bf46fa3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")
    # Nullable, no default → instant add (no table rewrite, no backfill).
    op.add_column("farm_member", sa.Column("invited_by", sa.Integer(), nullable=True))
    # SET NULL, not CASCADE — losing the inviter must not evict a legitimate member.
    op.create_foreign_key(
        op.f("fk_farm_member_invited_by_user"),
        "farm_member",
        "user",
        ["invited_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_farm_member_invited_by_user"), "farm_member", type_="foreignkey"
    )
    op.drop_column("farm_member", "invited_by")
