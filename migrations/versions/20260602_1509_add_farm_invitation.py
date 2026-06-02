"""add farm_invitation

Revision ID: 723c6bf46fa3
Revises: c9d0e1f2a3b4
Create Date: 2026-06-02 15:09:42.762623+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "723c6bf46fa3"
down_revision: str | None = "c9d0e1f2a3b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# farm_role already exists (created with farm_member) — reference it, never recreate.
farm_role = postgresql.ENUM("owner", "admin", "member", name="farm_role", create_type=False)
# invitation_status is new to this migration; created/dropped explicitly below.
invitation_status = postgresql.ENUM(
    "pending", "accepted", "revoked", name="invitation_status", create_type=False
)


def upgrade() -> None:
    invitation_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "farm_invitation",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("role", farm_role, nullable=False),
        sa.Column("status", invitation_status, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invited_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["farm_id"],
            ["farm.id"],
            name=op.f("fk_farm_invitation_farm_id_farm"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["invited_by"],
            ["user.id"],
            name=op.f("fk_farm_invitation_invited_by_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_farm_invitation")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_farm_invitation_token_hash")),
    )
    op.create_index(
        op.f("ix_farm_invitation_farm_invitation_email"),
        "farm_invitation",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_farm_invitation_farm_invitation_farm_id"),
        "farm_invitation",
        ["farm_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_farm_invitation_farm_invitation_farm_id"), table_name="farm_invitation"
    )
    op.drop_index(
        op.f("ix_farm_invitation_farm_invitation_email"), table_name="farm_invitation"
    )
    op.drop_table("farm_invitation")
    # farm_role is shared with farm_member; only drop the type this migration created.
    invitation_status.drop(op.get_bind(), checkfirst=True)
