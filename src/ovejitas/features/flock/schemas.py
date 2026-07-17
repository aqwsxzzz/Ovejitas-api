from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from ovejitas.core.schemas import OptionalStr, StrictModel


def _utc_now() -> datetime:
    return datetime.now(UTC)


class _FlockActionBase(StrictModel):
    occurred_at: datetime = Field(default_factory=_utc_now)
    # Headcount is whole animals — integer, never fractional (unlike material kg).
    quantity: int = Field(ge=1)


class FlockAcquisitionCreate(_FlockActionBase):
    # Optional — a flock can be received free or hatched; when present, the
    # action books a paired expense for the amount paid.
    amount: Decimal | None = Field(default=None, gt=0)
    # Optional per-entry currency; falls back to the farm's preferred currency.
    currency_id: int | None = None


class FlockSaleCreate(_FlockActionBase):
    amount: Decimal = Field(gt=0)
    currency_id: int | None = None
    buyer: OptionalStr = Field(default=None, max_length=255)


class FlockMortalityCreate(_FlockActionBase):
    cause: OptionalStr = Field(default=None, max_length=500)


class FlockActionRead(BaseModel):
    """The events a flock action emitted, plus the resulting on-hand headcount.

    ``paired_event_id`` is the expense (acquisition), income (sale), or
    mortality (mortality) event — null only for an acquisition with no amount.
    """

    inventory_event_id: int
    paired_event_id: int | None
    headcount: Decimal
