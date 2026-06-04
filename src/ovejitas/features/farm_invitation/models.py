from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Identity, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin
from ovejitas.features.farm_member.models import FarmRole


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"


class FarmInvitation(Base, TimestampMixin):
    __tablename__ = "farm_invitation"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farm.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    # SHA-256 hex digest of the opaque token; the plaintext is shown to the inviter once.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    role: Mapped[FarmRole] = mapped_column(
        # farm_role enum already exists (farm_member); don't recreate the type.
        SQLEnum(
            FarmRole,
            name="farm_role",
            create_type=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    status: Mapped[InvitationStatus] = mapped_column(
        SQLEnum(
            InvitationStatus,
            name="invitation_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=InvitationStatus.PENDING,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    invited_by: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
