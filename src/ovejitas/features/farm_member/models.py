from enum import StrEnum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Identity, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ovejitas.core.models import Base, TimestampMixin
from ovejitas.features.user.models import User


class FarmRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class FarmMember(Base, TimestampMixin):
    __tablename__ = "farm_member"
    __table_args__ = (UniqueConstraint("user_id", "farm_id", name="user_farm"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farm.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[FarmRole] = mapped_column(
        SQLEnum(FarmRole, name="farm_role", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    # Who invited this member (the "by"); NULL for owners self-created on farm creation.
    # SET NULL, not CASCADE — losing the inviter must not evict a legitimate member.
    invited_by: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Eager-loaded explicitly via selectinload; lazy="raise" guards against async lazy I/O.
    # foreign_keys pinned: invited_by also references user, so the path is ambiguous otherwise.
    user: Mapped[User] = relationship(lazy="raise", foreign_keys=[user_id])
