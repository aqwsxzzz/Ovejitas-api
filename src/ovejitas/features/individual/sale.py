"""Lifecycle of the INCOME event an individual's sale owns — the revenue entry
in its ledger, emitted when its status transitions to ``sold``.

The individual service calls these helpers; it never builds sale events by
hand. They emit / reconcile / reverse inside the caller's transaction — the
caller owns commit/rollback.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.core.errors import NotFoundError, ValidationError
from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.reversal import delete_event_if_exists
from ovejitas.features.event.types import EventType
from ovejitas.features.individual.models import Individual, IndividualStatus

_SALE_SOURCE = "sale"


def _sale_payload(buyer: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"source": _SALE_SOURCE}
    if buyer is not None:
        payload["buyer"] = buyer
    return payload


async def emit_sale(
    db: AsyncSession,
    *,
    individual: Individual,
    asset: Asset,
    occurred_at: datetime,
    amount: Decimal,
    currency: str,
    buyer: str | None,
    user_id: int,
) -> Event:
    """Emit the INCOME event for a sale. ``individual`` must already be flushed."""
    sale = Event(
        farm_id=asset.farm_id,
        asset_id=asset.id,
        individual_id=individual.id,
        type=EventType.INCOME,
        occurred_at=occurred_at,
        amount=amount,
        currency=currency,
        payload=_sale_payload(buyer),
        created_by=user_id,
    )
    db.add(sale)
    await db.flush()
    return sale


async def reconcile_sale(
    db: AsyncSession, *, individual: Individual, updates: dict[str, Any]
) -> None:
    """Sync the sale income event to edited sale details.

    ``updates`` holds only the sale keys actually sent in the PATCH.
    """
    sale = await db.get(Event, individual.sale_event_id)
    if sale is None:
        raise NotFoundError("Paired sale event missing")
    if "sold_at" in updates:
        sale.occurred_at = updates["sold_at"]
    if "sale_amount" in updates:
        sale.amount = updates["sale_amount"]
    if "buyer" in updates:
        sale.payload = _sale_payload(updates["buyer"])
    await db.flush()


async def reverse_sale(db: AsyncSession, *, individual: Individual) -> None:
    """Detach and delete the sale income event.

    The individual's FK column is cleared and flushed first so deleting the
    event does not trip its RESTRICT foreign key.
    """
    event_id = individual.sale_event_id
    individual.sale_event_id = None
    await db.flush()
    await delete_event_if_exists(db, event_id)
    await db.flush()


async def apply_sale(
    db: AsyncSession,
    *,
    asset: Asset,
    individual: Individual,
    new_status: IndividualStatus | None,
    updates: dict[str, Any],
    currency: str,
    user_id: int,
) -> None:
    """Emit, reconcile, or reverse the sale income event for a status change.

    Must run before ``individual.status`` is reassigned — it reads the current
    status to detect the transition.
    """
    was_sold = individual.status is IndividualStatus.SOLD
    will_be_sold = new_status is IndividualStatus.SOLD if new_status is not None else was_sold
    if not will_be_sold:
        if updates:
            raise ValidationError("sale_amount/sold_at/buyer are only valid for a sold individual")
        if was_sold:
            await reverse_sale(db, individual=individual)
        return
    if not was_sold:
        amount = updates.get("sale_amount")
        if amount is None:
            raise ValidationError("sale_amount is required when selling an individual")
        event = await emit_sale(
            db,
            individual=individual,
            asset=asset,
            occurred_at=updates.get("sold_at") or datetime.now(UTC),
            amount=amount,
            currency=currency,
            buyer=updates.get("buyer"),
            user_id=user_id,
        )
        individual.sale_event_id = event.id
    elif updates:
        await reconcile_sale(db, individual=individual, updates=updates)
