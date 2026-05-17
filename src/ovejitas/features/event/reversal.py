"""Generic event-reversal plumbing shared by feature `reverse_*` helpers."""

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.event.models import Event


async def delete_event_if_exists(db: AsyncSession, event_id: int | None) -> None:
    """Delete an event by id when it exists; a no-op for a None or missing id.

    The caller must clear any FK referencing the event and flush *before*
    calling this, or the event's RESTRICT foreign keys block the delete.
    """
    if event_id is None:
        return
    event = await db.get(Event, event_id)
    if event is not None:
        await db.delete(event)
