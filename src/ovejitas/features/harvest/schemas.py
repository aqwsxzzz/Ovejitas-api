from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.event.types import Unit


def _utc_now() -> datetime:
    return datetime.now(UTC)


class HarvestCreate(StrictModel):
    occurred_at: datetime = Field(default_factory=_utc_now)
    quantity: Decimal = Field(gt=0)
    unit: Unit
    category_id: int | None = None
    notes: OptionalStr = Field(default=None, max_length=500)


class HarvestRead(BaseModel):
    """The two events a harvest emitted, plus the produce asset's resulting
    on-hand balance in the harvested unit."""

    production_event_id: int
    inventory_event_id: int
    produce_balance: Decimal
