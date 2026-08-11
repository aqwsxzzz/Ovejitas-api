from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.event.types import AcquisitionMethod
from ovejitas.features.individual.models import IndividualStatus


def _utc_now() -> datetime:
    return datetime.now(UTC)


class IndividualCreate(StrictModel):
    tag: str = Field(min_length=1, max_length=128)
    name: OptionalStr = Field(default=None, max_length=255)
    birth_date: date | None = None
    mother_id: int | None = None
    father_id: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
    acquired_at: datetime = Field(default_factory=_utc_now)
    acquisition_method: AcquisitionMethod = AcquisitionMethod.OTHER
    amount: Decimal | None = Field(default=None, gt=0)
    # Optional per-entry currency for a purchased acquisition; falls back to the
    # farm's preferred currency.
    currency_id: int | None = None

    @model_validator(mode="after")
    def _amount_matches_method(self) -> Self:
        purchased = self.acquisition_method is AcquisitionMethod.PURCHASED
        if purchased and self.amount is None:
            raise ValueError("amount is required for a purchased acquisition")
        if not purchased and self.amount is not None:
            raise ValueError("amount is only valid for a purchased acquisition")
        return self


class IndividualUpdate(StrictModel):
    name: OptionalStr = Field(default=None, max_length=255)
    tag: str | None = Field(default=None, min_length=1, max_length=128)
    birth_date: date | None = None
    mother_id: int | None = None
    father_id: int | None = None
    status: IndividualStatus | None = None
    extra: dict[str, Any] | None = None
    acquired_at: datetime | None = None
    acquisition_method: AcquisitionMethod | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    # Optional per-entry currency for the acquisition/sale amount; falls back to
    # the farm's preferred currency.
    currency_id: int | None = None
    died_at: datetime | None = None
    cause: OptionalStr = Field(default=None, max_length=500)
    sale_amount: Decimal | None = Field(default=None, gt=0)
    sold_at: datetime | None = None
    buyer: OptionalStr = Field(default=None, max_length=255)


class IndividualRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    asset_id: int
    name: str | None
    tag: str
    birth_date: date | None
    mother_id: int | None
    father_id: int | None
    status: IndividualStatus
    extra: dict[str, Any]
    acquisition_event_id: int | None
    acquisition_expense_event_id: int | None
    mortality_event_id: int | None
    sale_event_id: int | None
    birth_event_id: int | None
    created_at: datetime
    updated_at: datetime


class IndividualFilters(FilterParams):
    status: IndividualStatus | None = None


class FarmIndividualFilters(IndividualFilters):
    """Filters for the farm-wide list. ``asset_id`` is meaningless on the
    per-asset route (the path already fixes it), so it lives only here."""

    asset_id: int | None = None


class OffspringCreate(StrictModel):
    tag: str = Field(min_length=1, max_length=128)
    name: OptionalStr = Field(default=None, max_length=255)
    birth_date: date | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class BirthCreate(StrictModel):
    occurred_at: datetime = Field(default_factory=_utc_now)
    father_id: int | None = None
    category_id: int | None = None
    notes: OptionalStr = Field(default=None, max_length=500)
    outcome: OptionalStr = Field(default=None, max_length=255)
    offspring: list[OffspringCreate] = Field(min_length=1)


class BirthRead(BaseModel):
    reproductive_event_id: int
    mother_id: int
    offspring: list[IndividualRead]
