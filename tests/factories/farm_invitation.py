from ovejitas.features.farm_invitation.models import FarmInvitation, InvitationStatus
from ovejitas.features.farm_member.models import FarmRole
from tests.factories._base import BaseFactory


class FarmInvitationFactory(BaseFactory):
    """Caller must pass `farm_id=`, `invited_by=`, `token_hash=`, `expires_at=`."""

    __model__ = FarmInvitation
    role = FarmRole.MEMBER
    status = InvitationStatus.PENDING
