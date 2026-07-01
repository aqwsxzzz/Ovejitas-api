"""backfill egg laying-rate + production into the product model

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-07-01 16:00:00.000000+00:00

Migrates the egg-specific model into the generic product model, so the new
production-productivity report shows historical eggs:

1. Create a per-farm "Huevos" production category (unit=unit) for every farm
   that has a coop with a laying rate configured.
2. Attribute existing uncategorised egg production (animal assets, unit/dozen)
   to that category.
3. Turn each coop's ``expected_eggs_per_head_per_day`` into a per_head_continuous
   target effective from the asset's creation date.

Data-only; the ``asset.expected_eggs_per_head_per_day`` column is dropped in the
next migration. Downgrade removes the created targets and Huevos categories —
which also nulls the category_id it backfilled (event FK is SET NULL).
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: str | None = "e1f2a3b4c5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. One "Huevos" production category per farm that has a rated coop.
    op.execute(
        """
        INSERT INTO event_category (farm_id, type, name, unit, created_at, updated_at)
        SELECT DISTINCT a.farm_id, 'production'::event_type, 'Huevos', 'unit'::unit, now(), now()
        FROM asset a
        WHERE a.expected_eggs_per_head_per_day IS NOT NULL
        ON CONFLICT (farm_id, type, name) DO NOTHING
        """
    )
    # 2. Attribute existing uncategorised egg production to that category.
    op.execute(
        """
        UPDATE event e
        SET category_id = c.id
        FROM asset a, event_category c
        WHERE e.asset_id = a.id
          AND a.kind = 'animal'
          AND e.type = 'production'
          AND e.unit IN ('unit', 'dozen')
          AND e.category_id IS NULL
          AND c.farm_id = a.farm_id
          AND c.type = 'production'
          AND c.name = 'Huevos'
        """
    )
    # 3. Turn each coop's laying rate into a per_head_continuous target.
    op.execute(
        """
        INSERT INTO asset_production_target
            (farm_id, asset_id, category_id, basis, expected_rate, period,
             effective_from, created_at, updated_at)
        SELECT a.farm_id, a.id, c.id, 'per_head_continuous'::production_basis,
               a.expected_eggs_per_head_per_day, 'day'::target_period,
               a.created_at::date, now(), now()
        FROM asset a
        JOIN event_category c
          ON c.farm_id = a.farm_id AND c.type = 'production' AND c.name = 'Huevos'
        WHERE a.expected_eggs_per_head_per_day IS NOT NULL
        ON CONFLICT (asset_id, category_id, effective_from) DO NOTHING
        """
    )


def downgrade() -> None:
    # Remove targets pointing at Huevos categories, then the categories (which
    # SET NULL the backfilled event.category_id via the event FK).
    op.execute(
        """
        DELETE FROM asset_production_target t
        USING event_category c
        WHERE t.category_id = c.id AND c.type = 'production' AND c.name = 'Huevos'
        """
    )
    op.execute(
        "DELETE FROM event_category WHERE type = 'production' AND name = 'Huevos'"
    )
