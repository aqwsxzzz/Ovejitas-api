from ovejitas.features.farm_member.models import FarmMember, FarmRole
from tests.factories._base import BaseFactory


class FarmMemberFactory(BaseFactory):
    """Caller must pass `user_id=` and `farm_id=` — FK generation is disabled."""

    __model__ = FarmMember
    role = FarmRole.MEMBER
