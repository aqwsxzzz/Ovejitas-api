from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.event.types import Unit


def _utc_now() -> datetime:
    return datetime.now(UTC)


class MaterialSaleCreate(StrictModel):
    occurred_at: datetime = Field(default_factory=_utc_now)
    quantity: Decimal = Field(gt=0)
    unit: Unit
    amount: Decimal = Field(gt=0)
    # Optional per-entry currency; falls back to the farm's preferred currency.
    currency_id: int | None = None
    buyer: OptionalStr = Field(default=None, max_length=255)
    category_id: int | None = None
    notes: OptionalStr = Field(default=None, max_length=500)


class MaterialSaleRead(BaseModel):
    """The two events a sale emitted, plus the material's resulting on-hand
    balance in the sold unit."""

    inventory_event_id: int
    income_event_id: int
    on_hand: Decimal
