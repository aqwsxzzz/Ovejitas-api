from sqlalchemy import CheckConstraint, Identity, String
from sqlalchemy.orm import Mapped, mapped_column

from ovejitas.core.models import Base, TimestampMixin


class Farm(Base, TimestampMixin):
    __tablename__ = "farm"
    __table_args__ = (
        CheckConstraint("char_length(default_currency) = 3", name="currency_iso4217_length"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    # IANA timezone name (e.g. "America/Montevideo"). Defines the farm's local
    # calendar day, which is the grain a produce pool's FIFO baskets group by —
    # a harvest logged at 23:30 local must land in that day's basket, not the
    # next UTC day's. Defaults to UTC; editable per farm.
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="UTC", server_default="UTC"
    )
