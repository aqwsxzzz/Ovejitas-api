from ovejitas.features.farm.models import Farm
from tests.factories._base import BaseFactory


class FarmFactory(BaseFactory):
    __model__ = Farm
    default_currency = "USD"

    @classmethod
    def name(cls) -> str:
        return f"{cls.__faker__.company()} Farm"
