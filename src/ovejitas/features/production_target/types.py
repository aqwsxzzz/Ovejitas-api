from enum import StrEnum


class ProductionBasis(StrEnum):
    """How a target's expected_rate scales into an expected quantity over a window.

    - ``per_head_continuous``: rate per head per ``period`` (eggs/day, milk/day) —
      scaled by animal-days in the window.
    - ``per_event``: expected yield per production event (shearing, harvest) —
      compared per event, not calendar-scaled.
    - ``total``: whole-asset expected yield (a crop field) — no headcount.
    """

    PER_HEAD_CONTINUOUS = "per_head_continuous"
    PER_EVENT = "per_event"
    TOTAL = "total"


class TargetPeriod(StrEnum):
    """The cadence a per_head_continuous rate is expressed in."""

    DAY = "day"
    YEAR = "year"
