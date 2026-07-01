from ovejitas.features.asset.models import Asset, AssetKind, AssetMode
from tests.factories._base import BaseFactory


class AssetFactory(BaseFactory):
    """Caller must pass `farm_id=`. Defaults to an aggregated animal asset."""

    __model__ = Asset
    kind = AssetKind.ANIMAL
    mode = AssetMode.AGGREGATED

    @classmethod
    def name(cls) -> str:
        return cls.__faker__.word().capitalize()
