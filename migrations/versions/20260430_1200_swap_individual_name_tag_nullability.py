"""swap_individual_name_tag_nullability

Revision ID: 7c1a2b3d4e5f
Revises: 0d352869af19
Create Date: 2026-04-30 12:00:00.000000+00:00

"""
from collections.abc import Sequence

from alembic import op

revision: str = "7c1a2b3d4e5f"
down_revision: str | None = "0d352869af19"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE individual SET tag = 'tag-' || id::text WHERE tag IS NULL"
    )
    op.alter_column("individual", "name", nullable=True)
    op.alter_column("individual", "tag", nullable=False)


def downgrade() -> None:
    op.execute(
        "UPDATE individual SET name = 'unnamed-' || id::text WHERE name IS NULL"
    )
    op.alter_column("individual", "tag", nullable=True)
    op.alter_column("individual", "name", nullable=False)
