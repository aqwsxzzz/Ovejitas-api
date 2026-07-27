"""realign each produce pool's name with the product that owns it

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8
Create Date: 2026-07-27 10:20:00.000000+00:00

Until now a pool took the product's name once, at creation, and never again:
renaming "Huevos" to "Huevos de gallina" moved the collection form and the
productivity report but left the stock screen, the sale screen and the
produce-outcome report on the old label. The API now renames both together;
this carries the products that already drifted onto the same footing.

Idempotent — the ``IS DISTINCT FROM`` skips pools already in agreement, so a
re-run touches nothing.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3d4e5f6a7b9"
down_revision: str | None = "b2c3d4e5f6a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE asset a
        SET name = c.name
        FROM event_category c
        WHERE c.produce_asset_id = a.id
          AND a.name IS DISTINCT FROM c.name
        """
    )


def downgrade() -> None:
    """No-op: the names this replaced are gone.

    A pool's old name lived only in its own row, so overwriting it was the whole
    point and there is nothing left to read it back from. Guessing one would be
    worse than leaving the pool named after its product.
    """
