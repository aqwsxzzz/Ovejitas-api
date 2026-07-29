"""pair each production category with its produce pool

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-07-27 10:10:00.000000+00:00

Data half of "a product owns its pool". Three steps, most-certain evidence first:

1. Pair a production category with the pool its harvests already deposited into,
   read from ``produce_lot`` -> the lot's production event -> its category.
2. Pair what is left with an unclaimed produce asset of the same farm and name —
   the hand-made twin this change exists to retire, matched before provisioning
   so a farm that never harvested does not end up with two "Huevos" pools.
3. Provision a pool for any production category still unpaired, so every product
   has somewhere to harvest into.

Aborts rather than guessing if the harvest history is ambiguous: a category whose
lots landed in two pools, or a pool fed by two categories, needs a human to
decide which is which. Both are impossible going forward — the API provisions the
pair together and the UNIQUE constraint holds the second case.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a8"
down_revision: str | None = "a1b2c3d4e5f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# One row per (category, pool) the harvest history actually links.
_PAIRS_FROM_HISTORY = """
    SELECT e.category_id AS category_id, pl.produce_asset_id AS produce_asset_id
    FROM produce_lot pl
    JOIN event e ON e.id = pl.production_event_id
    WHERE e.category_id IS NOT NULL
    GROUP BY e.category_id, pl.produce_asset_id
"""


def _assert_history_is_unambiguous(bind: sa.Connection) -> None:
    split_products = (
        bind.execute(
            sa.text(
                f"SELECT category_id FROM ({_PAIRS_FROM_HISTORY}) p "
                "GROUP BY category_id HAVING count(*) > 1"
            )
        )
        .scalars()
        .all()
    )
    if split_products:
        raise RuntimeError(
            f"event_category {sorted(split_products)} harvested into more than one produce "
            "asset. Pick the pool each product should keep, move the other's lots onto it, "
            "then re-run this migration."
        )

    shared_pools = (
        bind.execute(
            sa.text(
                f"SELECT produce_asset_id FROM ({_PAIRS_FROM_HISTORY}) p "
                "GROUP BY produce_asset_id HAVING count(*) > 1"
            )
        )
        .scalars()
        .all()
    )
    if shared_pools:
        raise RuntimeError(
            f"produce asset {sorted(shared_pools)} received harvests under more than one "
            "category. Split it into one pool per product, move each product's lots onto "
            "its own pool, then re-run this migration."
        )


def upgrade() -> None:
    _assert_history_is_unambiguous(op.get_bind())

    op.execute(
        f"""
        UPDATE event_category c
        SET produce_asset_id = p.produce_asset_id
        FROM ({_PAIRS_FROM_HISTORY}) p
        WHERE c.id = p.category_id
          AND c.type = 'production'
          AND c.produce_asset_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE event_category c
        SET produce_asset_id = a.id
        FROM asset a
        WHERE a.farm_id = c.farm_id
          AND a.kind = 'produce'
          AND a.name = c.name
          AND c.type = 'production'
          AND c.produce_asset_id IS NULL
          AND NOT EXISTS (
            SELECT 1 FROM event_category claimed WHERE claimed.produce_asset_id = a.id
          )
        """
    )

    # Name-matched back to its category: (farm_id, name) is unique within
    # type='production', so each returned pool re-joins exactly one row.
    op.execute(
        """
        WITH provisioned AS (
            INSERT INTO asset (farm_id, name, kind)
            SELECT c.farm_id, c.name, 'produce'
            FROM event_category c
            WHERE c.type = 'production' AND c.produce_asset_id IS NULL
            RETURNING id, farm_id, name
        )
        UPDATE event_category c
        SET produce_asset_id = provisioned.id
        FROM provisioned
        WHERE c.farm_id = provisioned.farm_id
          AND c.name = provisioned.name
          AND c.type = 'production'
          AND c.produce_asset_id IS NULL
        """
    )


def downgrade() -> None:
    """Unpair only.

    Pools provisioned by step 3 are left in place as ordinary produce assets:
    nothing distinguishes them from a pool the farm made by hand, so deleting on
    that guess would destroy real data. Re-running the upgrade re-pairs them by
    name in step 2 rather than creating duplicates.
    """
    op.execute("UPDATE event_category SET produce_asset_id = NULL")
