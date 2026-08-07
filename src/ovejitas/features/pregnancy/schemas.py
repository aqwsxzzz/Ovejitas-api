from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.pregnancy.guards import assert_pregnancy_projection


class PregnancyCreate(StrictModel):
    individual_id: int
    occurred_at: datetime
    is_pregnant: bool
    service_date: datetime | None = None
    sire_individual_id: int | None = None
    offspring_count: int | None = Field(default=None, ge=0)
    # Omit on a positive check to have it derived from the asset's gestation
    # length; a value supplied here is always kept as given.
    expected_due_at: datetime | None = None
    notes: OptionalStr = None
    idempotency_key: OptionalStr = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def _projection_rules(self) -> Self:
        assert_pregnancy_projection(self.is_pregnant, self.offspring_count, self.expected_due_at)
        return self


class PregnancyUpdate(StrictModel):
    """PATCH body. ``individual_id`` is immutable — a different individual is a
    different pregnancy record. The non-pregnant projection rule is enforced on
    the merged state in the service. ``expected_due_at`` is never re-derived
    here: editing ``service_date`` leaves an already-stored due date alone."""

    occurred_at: datetime | None = None
    is_pregnant: bool | None = None
    service_date: datetime | None = None
    sire_individual_id: int | None = None
    offspring_count: int | None = Field(default=None, ge=0)
    expected_due_at: datetime | None = None
    notes: OptionalStr = None


class PregnancyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    individual_id: int
    reproductive_event_id: int
    occurred_at: datetime
    is_pregnant: bool
    service_date: datetime | None
    sire_individual_id: int | None
    offspring_count: int | None
    expected_due_at: datetime | None
    notes: str | None
    idempotency_key: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime


class PregnancyFilters(FilterParams):
    individual_id: int | None = None
    sire_individual_id: int | None = None
    is_pregnant: bool | None = None
