from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ovejitas.core.filters import FilterParams
from ovejitas.core.schemas import OptionalStr, StrictModel
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit


class _EventCreateBase(StrictModel):
    occurred_at: datetime
    individual_id: int | None = None
    category_id: int | None = None
    notes: OptionalStr = None
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: OptionalStr = Field(default=None, max_length=128)


class EventProductionCreate(_EventCreateBase):
    type: Literal[EventType.PRODUCTION]
    # Required: production is attributed to a product (a production category) so
    # the productivity report can compute produced-vs-expected. Going forward.
    category_id: int
    quantity: Decimal = Field(gt=0)
    unit: Unit


class EventExpenseCreate(_EventCreateBase):
    type: Literal[EventType.EXPENSE]
    amount: Decimal = Field(gt=0)
    # Optional per-entry currency; falls back to the farm's preferred currency.
    currency_id: int | None = None


class EventIncomeCreate(_EventCreateBase):
    type: Literal[EventType.INCOME]
    amount: Decimal = Field(gt=0)
    currency_id: int | None = None


class EventObservationCreate(_EventCreateBase):
    type: Literal[EventType.OBSERVATION]


class EventReproductiveCreate(_EventCreateBase):
    type: Literal[EventType.REPRODUCTIVE]
    individual_id: int


# NOTE: ACQUISITION and MORTALITY events are deliberately absent from EventCreate.
# They are owned by individual lifecycle actions (IndividualService.create /
# .update) and must never be hand-written via POST /events — see Philosophy 1.


class EventInventoryCreate(_EventCreateBase):
    type: Literal[EventType.INVENTORY]
    adjustment: InventoryAdjustment
    quantity: Decimal = Field(ge=0)
    unit: Unit

    @model_validator(mode="after")
    def _quantity_required_for_non_reset(self) -> Self:
        if self.adjustment is not InventoryAdjustment.RESET and self.quantity <= 0:
            raise ValueError("increment/decrement require quantity > 0")
        return self


EventCreate = Annotated[
    EventProductionCreate
    | EventExpenseCreate
    | EventIncomeCreate
    | EventObservationCreate
    | EventReproductiveCreate
    | EventInventoryCreate,
    Field(discriminator="type"),
]


class EventUpdate(StrictModel):
    occurred_at: datetime | None = None
    individual_id: int | None = None
    category_id: int | None = None
    quantity: Decimal | None = Field(default=None, ge=0)
    unit: Unit | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    adjustment: InventoryAdjustment | None = None
    notes: OptionalStr = None
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
    currency_id: int | None
    adjustment: InventoryAdjustment | None
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
    adjustment: InventoryAdjustment | None = None


class InventoryBalanceRow(BaseModel):
    unit: Unit
    on_hand: Decimal
    last_reset_at: datetime | None


class InventoryBalance(BaseModel):
    asset_id: int
    balances: list[InventoryBalanceRow]
