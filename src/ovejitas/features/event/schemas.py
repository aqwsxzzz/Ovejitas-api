from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ovejitas.core.filters import FilterParams
from ovejitas.features.event.types import EventType, Unit


class _EventCreateBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime
    individual_id: int | None = None
    category_id: int | None = None
    notes: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=128)


class EventProductionCreate(_EventCreateBase):
    type: Literal[EventType.PRODUCTION]
    quantity: Decimal = Field(gt=0)
    unit: Unit


class EventExpenseCreate(_EventCreateBase):
    type: Literal[EventType.EXPENSE]
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)


class EventIncomeCreate(_EventCreateBase):
    type: Literal[EventType.INCOME]
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)


class EventObservationCreate(_EventCreateBase):
    type: Literal[EventType.OBSERVATION]


class EventReproductiveCreate(_EventCreateBase):
    type: Literal[EventType.REPRODUCTIVE]
    individual_id: int


class EventAcquisitionCreate(_EventCreateBase):
    type: Literal[EventType.ACQUISITION]
    quantity: Decimal = Field(gt=0)
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class EventMortalityCreate(_EventCreateBase):
    type: Literal[EventType.MORTALITY]
    quantity: Decimal = Field(gt=0)


EventCreate = Annotated[
    EventProductionCreate
    | EventExpenseCreate
    | EventIncomeCreate
    | EventObservationCreate
    | EventReproductiveCreate
    | EventAcquisitionCreate
    | EventMortalityCreate,
    Field(discriminator="type"),
]


class EventUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime | None = None
    individual_id: int | None = None
    category_id: int | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    unit: Unit | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    notes: str | None = None
    payload: dict[str, Any] | None = None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    asset_id: int
    individual_id: int | None
    type: EventType
    category_id: int | None
    occurred_at: datetime
    quantity: Decimal | None
    unit: Unit | None
    amount: Decimal | None
    currency: str | None
    notes: str | None
    payload: dict[str, Any]
    idempotency_key: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime


class EventFilters(FilterParams):
    type: EventType | None = None
    category_id: int | None = None
    individual_id: int | None = None
