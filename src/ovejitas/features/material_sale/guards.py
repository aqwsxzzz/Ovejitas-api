"""Cross-entity validation for the material sale action."""

from ovejitas.core.errors import ValidationError
from ovejitas.features.asset.models import Asset, AssetKind


def validate_sale_asset(asset: Asset) -> None:
    """Only stock-bearing material assets are sold this way — animal sales are
    the flock and individual actions."""
    if asset.kind is not AssetKind.MATERIAL:
        raise ValidationError("Material sales require a material asset")
