"""Central model registry so Alembic picks up every table via Base.metadata."""

from ovejitas.core.models import Base
from ovejitas.features.asset.models import Asset, AssetKind, AssetMode
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.event_category.models import EventCategory
from ovejitas.features.farm.models import Farm
from ovejitas.features.farm_member.models import FarmMember, FarmRole
from ovejitas.features.individual.models import Individual, IndividualStatus
from ovejitas.features.user.models import User

__all__ = [
    "Asset",
    "AssetKind",
    "AssetMode",
    "Base",
    "Event",
    "EventCategory",
    "EventType",
    "Farm",
    "FarmMember",
    "FarmRole",
    "Individual",
    "IndividualStatus",
    "User",
]
