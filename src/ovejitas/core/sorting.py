from typing import Any

from sqlalchemy import Select
from sqlalchemy.orm import InstrumentedAttribute

from ovejitas.core.errors import ValidationError


def apply_sort(
    stmt: Select[Any],
    sort: str | None,
    allowed: dict[str, InstrumentedAttribute[Any]],
) -> Select[Any]:
    """Apply `?sort=-created_at,name` to a SELECT, whitelisting columns.

    `-` prefix = DESC, no prefix = ASC. Unknown fields raise ValidationError.
    """
    if not sort:
        return stmt
    for raw in sort.split(","):
        field = raw.strip()
        if not field:
            continue
        descending = field.startswith("-")
        name = field.lstrip("-")
        column = allowed.get(name)
        if column is None:
            raise ValidationError(f"Invalid sort field: {name}")
        stmt = stmt.order_by(column.desc() if descending else column.asc())
    return stmt
