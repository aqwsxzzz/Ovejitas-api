"""Cross-entity validation for flock actions."""

from ovejitas.core.errors import ValidationError
from ovejitas.features.asset.models import Asset, AssetKind, AssetMode


def validate_flock_asset(asset: Asset) -> None:
    """A flock is an animal asset counted in aggregate — the only asset shape
    the acquisition/sale/mortality actions operate on."""
    if asset.kind is not AssetKind.ANIMAL or asset.mode is not AssetMode.AGGREGATED:
        raise ValidationError("Flock actions require an animal asset in aggregated mode")
