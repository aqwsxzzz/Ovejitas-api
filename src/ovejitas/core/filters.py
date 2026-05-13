from datetime import datetime
from typing import Any

from sqlalchemy import Select
from sqlalchemy.orm import InstrumentedAttribute

from ovejitas.core.schemas import StrictModel


class FilterParams(StrictModel):
    """Base filter schema. Feature-specific filters extend this."""

    date_from: datetime | None = None
    date_to: datetime | None = None


def apply_date_range(
    stmt: Select[Any],
    column: InstrumentedAttribute[Any],
    date_from: datetime | None,
    date_to: datetime | None,
) -> Select[Any]:
    if date_from is not None:
        stmt = stmt.where(column >= date_from)
    if date_to is not None:
        stmt = stmt.where(column <= date_to)
    return stmt
