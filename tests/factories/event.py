from datetime import UTC, datetime
from decimal import Decimal
from typing import ClassVar

from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, Unit
from tests.factories._base import BaseFactory


class EventFactory(BaseFactory):
    """Caller must pass `farm_id=`, `asset_id=`, and `created_by=` (user id).

    Default shape is a production event — override `type` and related columns
    (quantity/amount/etc) per test.
    """

    __model__ = Event
    type = EventType.PRODUCTION
    quantity = Decimal("1")
    unit = Unit.UNIT
    payload: ClassVar[dict[str, object]] = {}

    @classmethod
    def occurred_at(cls) -> datetime:
        return datetime.now(UTC)
