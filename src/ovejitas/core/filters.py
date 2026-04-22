from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Select
from sqlalchemy.orm import InstrumentedAttribute


class FilterParams(BaseModel):
    """Base filter schema. Feature-specific filters extend this."""

    model_config = ConfigDict(extra="forbid")

    date_from: datetime | None = None
    date_to: datetime | None = None


def apply_date_range(
    stmt: Select,
    column: InstrumentedAttribute,
    date_from: datetime | None,
    date_to: datetime | None,
) -> Select:
    if date_from is not None:
        stmt = stmt.where(column >= date_from)
    if date_to is not None:
        stmt = stmt.where(column <= date_to)
    return stmt
