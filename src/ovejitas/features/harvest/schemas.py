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
    # The harvest names only the product. Its pool is resolved from
    # ``event_category.produce_asset_id``, so the destination cannot disagree with
    # what the production event is attributed to. One producer can still feed
    # several products by harvesting each under its own category.
    category_id: int
    notes: OptionalStr = Field(default=None, max_length=500)


class HarvestRead(BaseModel):
    """The two events a harvest emitted, plus the produce asset's resulting
    on-hand balance in the harvested unit."""

    production_event_id: int
    inventory_event_id: int
    produce_balance: Decimal
