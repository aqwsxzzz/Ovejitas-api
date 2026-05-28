from typing import Any

from sqlalchemy import Select, or_
from sqlalchemy.orm import InstrumentedAttribute


def apply_search(
    stmt: Select[Any],
    term: str | None,
    columns: list[InstrumentedAttribute[Any]],
) -> Select[Any]:
    """Apply case-insensitive `q` search across a whitelisted column set."""
    if not term or not columns:
        return stmt
    pattern = f"%{term.strip()}%"
    return stmt.where(or_(*(column.ilike(pattern) for column in columns)))
