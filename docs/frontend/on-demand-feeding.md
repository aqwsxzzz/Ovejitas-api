# Frontend Guide — On-demand feeding (no per-day config)

> Origin: farm-owner feedback — *"La configuración manual de alimento en gallinas
> no sirve, no se da de comer por día, se alimenta a demanda. Habría que agregar
> un gasto de X cantidad de kilos en el momento que se da de comer y ya."*

The owner is right, and **the backend already works this way.** There is no
per‑day feed schedule in the API — feeding is recorded **on demand**, one event
at the moment food is given. The "manual daily feed config" to remove lives
entirely in the frontend. The API contract is in
[`docs/api/material-consumptions.yaml`](../api/material-consumptions.yaml); this
doc covers the **flow**.

All paths are under `/api/v1`; authenticated calls send `Authorization: Bearer <token>`.

---

## Concept

Feed is a regular `Asset` (`kind=material`, e.g. "Maíz molido") that holds stock.
Two actions, both already implemented:

- **Stock the feed** — `material-purchases` adds kilos *and* a cost basis.
- **Feed the animals** — `material-consumptions` with `reason=feeding` removes
  kilos at the moment of feeding and attributes the cost to the coop.

Cost flows automatically into the `cost-per-unit` report via purchase averaging —
**you do not record a separate expense.**

---

## What to change in the UI

Remove the "daily feed allocation / schedule" screen. Replace it with a single
**"Registrar alimentación"** action on a coop, defaulting the timestamp to *now*:

| Field      | Source                                                        |
|------------|--------------------------------------------------------------|
| Feed       | pick an `asset` with `kind=material` that has stock           |
| Coop       | the consumer `asset` (prefilled if opened from a coop)        |
| Kilos      | free number input                                             |
| When       | datetime, default **now**                                    |

### Register a feeding

```
POST /api/v1/farms/{farm_id}/material-consumptions
{
  "material_asset_id": 42,        // the feed
  "consumer_asset_id": 7,         // the coop being fed  (REQUIRED for feeding)
  "occurred_at": "2026-06-14T11:00:00Z",
  "quantity": "15",               // kilos given right now
  "unit": "kg",
  "reason": "feeding"
}
```

`201` returns the consumption; stock is decremented atomically via a paired
inventory event.

### Errors to handle

- **`409 insufficient_stock`** — not enough feed on hand. Prompt the user to
  register a purchase first (see below).
- **`422`** — `consumer_asset_id` missing (it's mandatory when `reason=feeding`),
  or `unit` doesn't match the unit the feed is stocked in.

### Optional: idempotency

Send a client‑generated `idempotency_key` to make a double‑tap safe — replaying
the same key returns the original record with `200` instead of creating a second
feeding.

---

## Prerequisite — keep the feed stocked (and valued)

For the cost report to value the feed, stock must arrive via a **purchase**, not a
manual inventory bump:

```
POST /api/v1/farms/{farm_id}/material-purchases
{
  "material_asset_id": 42,
  "occurred_at": "2026-06-01T10:00:00Z",
  "quantity": "100",     // kg bought
  "unit": "kg",
  "amount": "200"        // total paid → average cost 2/kg
}
```

Feed that was added by a bare inventory event has no cost basis; consuming it
still works, but the cost report flags it (`has_unvalued_consumption: true`).

---

## Why this matches the feedback

- *"No se da de comer por día"* → there is no per‑day model to fight; you log a
  feeding only when it happens.
- *"Agregar un gasto de X kilos en el momento que se da de comer"* → that **is**
  a `material-consumption` with `reason=feeding`; the kilos leave stock and the
  money is attributed through the original purchase price. One call, done.
```
