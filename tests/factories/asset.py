from ovejitas.features.asset.models import Asset, AssetKind, AssetMode
from tests.factories._base import BaseFactory


class AssetFactory(BaseFactory):
    """Caller must pass `farm_id=`. Defaults to an aggregated animal asset."""

    __model__ = Asset
    kind = AssetKind.ANIMAL
    mode = AssetMode.AGGREGATED
    # Left unset by default: a random int would break the 20-400 sanity CHECK,
    # and most tests do not care how long this animal gestates.
    gestation_days = None
    # Active by default: a random timestamp here would archive the asset and
    # drop it out of every default list.
    archived_at = None

    @classmethod
    def name(cls) -> str:
        return cls.__faker__.word().capitalize()
