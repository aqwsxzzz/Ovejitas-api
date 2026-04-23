from ovejitas.features.event.types import EventType
from ovejitas.features.event_category.models import EventCategory
from tests.factories._base import BaseFactory


class EventCategoryFactory(BaseFactory):
    """Caller must pass `farm_id=`."""

    __model__ = EventCategory
    type = EventType.PRODUCTION

    @classmethod
    def name(cls) -> str:
        return cls.__faker__.word()
