"""Supported ISO 4217 currency codes.

A farm can only enable currencies from this allowlist. The set is intentionally
scoped to the markets Ovejitas serves; extend it here when a new market is added.
"""

SUPPORTED_CURRENCIES: frozenset[str] = frozenset(
    {
        "USD",  # US Dollar
        "EUR",  # Euro
        "GBP",  # Pound Sterling
        "ARS",  # Argentine Peso
        "UYU",  # Uruguayan Peso
        "BRL",  # Brazilian Real
        "CLP",  # Chilean Peso
        "PYG",  # Paraguayan Guaraní
        "MXN",  # Mexican Peso
        "COP",  # Colombian Peso
        "PEN",  # Peruvian Sol
    }
)


def normalize_code(code: str) -> str:
    """Uppercase a code and assert it is a supported ISO 4217 currency."""
    normalized = code.upper()
    if normalized not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Unsupported currency code: {code!r}")
    return normalized
