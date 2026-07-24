"""Cross-entity validation for the material sale action."""

from ovejitas.core.errors import ValidationError
from ovejitas.features.asset.models import INVENTORY_KINDS, Asset


def validate_sale_asset(asset: Asset) -> None:
    """Only stock-bearing assets are sold this way — produce (eggs, milk) or
    surplus materials (feed). Animal sales are the flock and individual actions."""
    if asset.kind not in INVENTORY_KINDS:
        raise ValidationError("Material sales require a material or produce asset")
