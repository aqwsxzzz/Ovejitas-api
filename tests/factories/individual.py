from typing import ClassVar

from ovejitas.features.individual.models import Individual, IndividualStatus
from tests.factories._base import BaseFactory


class IndividualFactory(BaseFactory):
    """Caller must pass `farm_id=` and `asset_id=`."""

    __model__ = Individual
    status = IndividualStatus.ACTIVE
    extra: ClassVar[dict[str, object]] = {}

    @classmethod
    def name(cls) -> str:
        return cls.__faker__.first_name()

    @classmethod
    def tag(cls) -> str:
        return cls.__faker__.unique.bothify(text="TAG-####")
