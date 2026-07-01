"""add event_category.unit (product unit of measure)

Revision ID: d7e8f9a0b1c2
Revises: bfe60ab136f0
Create Date: 2026-07-01 10:00:00.000000+00:00

Promotes production categories toward first-class "products" by giving each a
unit of measure. Nullable: unit is only meaningful for production categories,
and "required for production" is enforced at the API layer (going forward), not
by a DB constraint — existing rows stay valid.

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7e8f9a0b1c2"
down_revision: str | None = "bfe60ab136f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")
    # Reuse the existing `unit` PG enum (created in 20260430_1500_typed_event_unit).
    # Nullable, no default → instant add (no table rewrite, no backfill).
    op.execute("ALTER TABLE event_category ADD COLUMN unit unit")


def downgrade() -> None:
    # Drop only the column — the `unit` enum type is shared with `event.unit`.
    op.execute("ALTER TABLE event_category DROP COLUMN unit")
