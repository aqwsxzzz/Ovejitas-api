"""add_asset_archived_at

Retirement for assets. An asset with events cannot change kind or mode (that
rule keeps recorded history meaningful) and cannot be deleted once it carries
harvests, feed consumption or a product's pool (six RESTRICT foreign keys say
so). Together that left a sold flock permanently immutable and permanently
present in every list, picker and target selector. Archiving is the operation
the farmer actually wanted: it destroys nothing and hides nothing that history
still needs.

Nullable with no default, so existing rows fill instantly and read as active.

Revision ID: e5f6a7b8c9db
Revises: d4e5f6a7b8ca
Create Date: 2026-08-11 10:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9db"
down_revision: str | None = "d4e5f6a7b8ca"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("asset", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("asset", "archived_at")
