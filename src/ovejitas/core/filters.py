from datetime import datetime, time, timedelta
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
        # A date-only upper bound arrives as midnight (00:00). Comparing it with
        # an inclusive `<= midnight` drops every same-day event logged later that
        # day, which makes an in-progress period look empty. Roll a midnight
        # bound forward to the next midnight and compare exclusively so the whole
        # day is covered regardless of event time-of-day. A bound with an
        # explicit time keeps its exact `<=` meaning.
        if date_to.time() == time():
            stmt = stmt.where(column < date_to + timedelta(days=1))
        else:
            stmt = stmt.where(column <= date_to)
    return stmt
