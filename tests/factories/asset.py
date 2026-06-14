from ovejitas.features.asset.models import Asset, AssetKind, AssetMode
from tests.factories._base import BaseFactory


class AssetFactory(BaseFactory):
    """Caller must pass `farm_id=`. Defaults to an aggregated animal asset."""

    __model__ = Asset
    kind = AssetKind.ANIMAL
    mode = AssetMode.AGGREGATED
    # Laying rate is opt-in — leave it unset unless a test configures it,
    # otherwise polyfactory would invent out-of-range NUMERIC values.
    expected_eggs_per_head_per_day = None

    @classmethod
    def name(cls) -> str:
        return cls.__faker__.word().capitalize()
