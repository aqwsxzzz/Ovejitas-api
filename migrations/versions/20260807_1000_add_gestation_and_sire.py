"""add_gestation_and_sire

Gestation length on the animal asset, so a positive pregnancy check no longer
depends on a farmer hand-typing the due date — a check saved without one is
invisible to the upcoming-births report forever. Plus the two facts that had
nowhere to live on a check: who bred her, and when she was served. The service
date is what makes the derived due date honest; counting from the check date
alone is wrong for any check performed after conception.

All three columns are nullable with no default, so existing rows fill instantly
and behave exactly as before.

Revision ID: d4e5f6a7b8ca
Revises: c3d4e5f6a7b9
Create Date: 2026-08-07 10:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8ca"
down_revision: str | None = "c3d4e5f6a7b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("asset", sa.Column("gestation_days", sa.Integer(), nullable=True))
    op.create_check_constraint(
        op.f("ck_asset_gestation_days_sane"),
        "asset",
        "gestation_days IS NULL OR gestation_days BETWEEN 20 AND 400",
    )
    op.add_column(
        "pregnancy", sa.Column("service_date", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("pregnancy", sa.Column("sire_individual_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_pregnancy_sire_individual_id"), "pregnancy", ["sire_individual_id"]
    )
    op.create_foreign_key(
        op.f("fk_pregnancy_sire_individual_id_individual"),
        "pregnancy",
        "individual",
        ["sire_individual_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_pregnancy_sire_individual_id_individual"), "pregnancy", type_="foreignkey"
    )
    op.drop_index(op.f("ix_pregnancy_sire_individual_id"), table_name="pregnancy")
    op.drop_column("pregnancy", "sire_individual_id")
    op.drop_column("pregnancy", "service_date")
    op.drop_constraint(op.f("ck_asset_gestation_days_sane"), "asset", type_="check")
    op.drop_column("asset", "gestation_days")
