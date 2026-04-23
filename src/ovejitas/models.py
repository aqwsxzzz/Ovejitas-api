"""Central model registry so Alembic picks up every table via Base.metadata."""

from ovejitas.core.models import Base
from ovejitas.features.farm.models import Farm
from ovejitas.features.farm_member.models import FarmMember, FarmRole
from ovejitas.features.user.models import User

__all__ = ["Base", "Farm", "FarmMember", "FarmRole", "User"]
