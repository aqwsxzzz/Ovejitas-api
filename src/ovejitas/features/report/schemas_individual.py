"""Schemas for the per-individual reports — upcoming births and the event
timeline of one animal."""

from datetime import datetime

from pydantic import BaseModel

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import EventType


class UpcomingBirthsQuery(FilterParams):
    # The window is required: the report answers "which individuals are due
    # between these two dates". Overriding the optional base fields makes them
    # required query params (422 if missing), validated by FastAPI itself.
    date_from: datetime
    date_to: datetime


class UpcomingBirthRow(BaseModel):
    individual_id: int
    individual_tag: str
    asset_id: int
    expected_due_at: datetime
    offspring_count: int | None
    # whole days from the window start (date_from) to the expected due date
    days_until_due: int


class UpcomingBirthsReport(BaseModel):
    data: list[UpcomingBirthRow]


class TimelineQuery(FilterParams):
    type: EventType | None = None
