from datetime import datetime, time, timedelta
from typing import Any, Self
from zoneinfo import ZoneInfo

from sqlalchemy import Select
from sqlalchemy.orm import InstrumentedAttribute

from ovejitas.core.schemas import StrictModel


def _anchor(value: datetime | None, tz: ZoneInfo) -> datetime | None:
    """Read a naive bound as farm-local wall clock; leave an aware one alone."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=tz)


class FilterParams(StrictModel):
    """Base filter schema. Feature-specific filters extend this."""

    date_from: datetime | None = None
    date_to: datetime | None = None

    def localized(self, tz: ZoneInfo) -> Self:
        """The same window, with naive bounds anchored to the farm's timezone.

        A client sending ``date_to=2026-07-26`` means that day on the farm's
        calendar, not UTC's. Anchoring here is what lets the midnight rolling in
        ``apply_date_range`` land on a *local* day boundary. A bound that already
        carries an offset names an exact instant, so it is preserved as sent.
        """
        return self.model_copy(
            update={
                "date_from": _anchor(self.date_from, tz),
                "date_to": _anchor(self.date_to, tz),
            }
        )


def _require_aware(value: datetime | None, name: str) -> None:
    if value is not None and value.tzinfo is None:
        raise ValueError(
            f"{name} must be timezone-aware — wire the route through farm_local() "
            "so naive bounds are anchored to the farm's timezone"
        )


def apply_date_range(
    stmt: Select[Any],
    column: InstrumentedAttribute[Any],
    date_from: datetime | None,
    date_to: datetime | None,
) -> Select[Any]:
    """Bound a ``timestamptz`` column by an already-localized window.

    Bounds must be timezone-aware. Routes get that from ``farm_local()``, which
    anchors naive input to the farm's zone; a naive bound reaching here would be
    read as UTC by the driver and silently shift every day boundary, so it is
    rejected as the wiring bug it is rather than quietly mis-answered.

    Both bounds stay bare comparisons against the column, so its index remains
    usable — the timezone lives in the Python-side values, never in a function
    wrapped around the column.
    """
    _require_aware(date_from, "date_from")
    _require_aware(date_to, "date_to")
    if date_from is not None:
        stmt = stmt.where(column >= date_from)
    if date_to is not None:
        # A date-only upper bound arrives as local midnight (00:00). Comparing it
        # with an inclusive `<= midnight` drops every same-day event logged later
        # that day, which makes an in-progress period look empty. Roll a midnight
        # bound forward to the next local midnight and compare exclusively so the
        # whole day is covered regardless of event time-of-day. Adding a day to an
        # aware datetime advances the wall clock, so the roll follows the farm's
        # calendar across any offset change. A bound with an explicit time keeps
        # its exact `<=` meaning.
        if date_to.time() == time():
            stmt = stmt.where(column < date_to + timedelta(days=1))
        else:
            stmt = stmt.where(column <= date_to)
    return stmt
