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
