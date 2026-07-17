"""currency as a first-class per-farm resource

Introduces a ``currency`` table (one row per enabled ISO code per farm) and
repoints the monetary columns at it by id:

* ``event.currency`` (String(3), nullable)      -> ``event.currency_id`` (FK, nullable)
* ``material_purchase.currency`` (String(3))    -> ``material_purchase.currency_id`` (FK, NOT NULL)

``farm.default_currency`` (String(3)) is intentionally kept — it stays the
farm's preferred-currency *pointer*, resolved to a currency row by code when an
entry omits ``currency_id``.

Backfill runs in the single migration transaction: a currency row is seeded per
distinct code already used (across events, purchases, and each farm's default),
then every monetary row's ``currency_id`` is backfilled by matching (farm, code).
No monetary history is stranded. FKs use ON DELETE RESTRICT so a referenced
currency can never be hard-deleted out from under the ledger.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "a3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("SET lock_timeout = '5s'")

    op.create_table(
        "currency",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "farm_id",
            sa.Integer(),
            sa.ForeignKey("farm.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=8), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.UniqueConstraint("farm_id", "code", name="farm_code"),
    )
    op.create_index("ix_currency_farm_id", "currency", ["farm_id"])

    # Seed one currency per distinct code already in use, per farm — including
    # every farm's preferred code even if no event used it yet. name defaults to
    # the code (a human name can be edited later via the API).
    op.execute(
        """
        INSERT INTO currency (farm_id, code, name)
        SELECT farm_id, code, code FROM (
            SELECT farm_id, currency AS code FROM event WHERE currency IS NOT NULL
            UNION
            SELECT farm_id, currency AS code FROM material_purchase
            UNION
            SELECT id AS farm_id, default_currency AS code FROM farm
        ) used
        """
    )

    # event.currency_id — nullable (non-monetary events carry no currency).
    op.add_column("event", sa.Column("currency_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_event_currency_id_currency",
        "event",
        "currency",
        ["currency_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.execute(
        """
        UPDATE event e SET currency_id = c.id
        FROM currency c
        WHERE c.farm_id = e.farm_id AND c.code = e.currency AND e.currency IS NOT NULL
        """
    )
    op.create_index("ix_event_currency_id", "event", ["currency_id"])

    # material_purchase.currency_id — added nullable, backfilled, then constrained.
    op.add_column("material_purchase", sa.Column("currency_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_material_purchase_currency_id_currency",
        "material_purchase",
        "currency",
        ["currency_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.execute(
        """
        UPDATE material_purchase m SET currency_id = c.id
        FROM currency c
        WHERE c.farm_id = m.farm_id AND c.code = m.currency
        """
    )
    op.alter_column("material_purchase", "currency_id", nullable=False)
    op.create_index("ix_material_purchase_currency_id", "material_purchase", ["currency_id"])

    op.drop_column("event", "currency")
    op.drop_column("material_purchase", "currency")


def downgrade() -> None:
    op.execute("SET lock_timeout = '5s'")

    # Re-add the string columns and restore codes from the currency rows.
    op.add_column("event", sa.Column("currency", sa.String(length=3), nullable=True))
    op.execute("UPDATE event e SET currency = c.code FROM currency c WHERE c.id = e.currency_id")

    op.add_column(
        "material_purchase", sa.Column("currency", sa.String(length=3), nullable=True)
    )
    op.execute(
        "UPDATE material_purchase m SET currency = c.code FROM currency c WHERE c.id = m.currency_id"
    )
    op.alter_column("material_purchase", "currency", nullable=False)

    op.drop_index("ix_material_purchase_currency_id", "material_purchase")
    op.drop_constraint(
        "fk_material_purchase_currency_id_currency", "material_purchase", type_="foreignkey"
    )
    op.drop_column("material_purchase", "currency_id")

    op.drop_index("ix_event_currency_id", "event")
    op.drop_constraint("fk_event_currency_id_currency", "event", type_="foreignkey")
    op.drop_column("event", "currency_id")

    op.drop_index("ix_currency_farm_id", "currency")
    op.drop_table("currency")
