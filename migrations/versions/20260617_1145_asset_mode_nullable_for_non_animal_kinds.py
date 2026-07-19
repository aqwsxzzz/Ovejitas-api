"""asset mode nullable for non-animal kinds

Revision ID: 231b2506dedc
Revises: c5d6e7f8a9b0
Create Date: 2026-06-17 11:45:34.111588+00:00

Only animals carry a tracking mode (aggregated/individual); material,
equipment, location and crop assets leave it null. Existing rows keep their
current mode and remain readable — the downgrade re-imposes NOT NULL, so it
only succeeds while no row has a null mode.
"""
from collections.abc import Sequence

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '231b2506dedc'
down_revision: str | None = 'c5d6e7f8a9b0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        'asset',
        'mode',
        existing_type=postgresql.ENUM('aggregated', 'individual', name='asset_mode'),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'asset',
        'mode',
        existing_type=postgresql.ENUM('aggregated', 'individual', name='asset_mode'),
        nullable=False,
    )
