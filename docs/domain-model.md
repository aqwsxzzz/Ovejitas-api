# Domain Model

Reference doc for the three-primitive event-sourced model. If the code and this doc disagree, the code wins — open a PR to fix the doc.

Companion to [domain-rebuild-plan.md](./domain-rebuild-plan.md) and [prd_granjas.md](./prd_granjas.md). Inspired by the [farmOS Asset + Log model](https://farmos.org/model/).

## Primitives

Three tables carry the domain. Everything else is scaffolding.

- **`asset`** — any trackable thing on a farm: animals, crops, equipment, materials, locations. Has a `kind` (UI classifier) and a `mode` (`aggregated` for bulk/count, `individual` for tagged instances).
- **`individual`** — one tagged instance of an `individual`-mode asset. Optional. Only created when you need to track a specific animal/machine/plant with parentage, tag, birth date, status.
- **`event`** — one fact that happened against an asset (and optionally a specific individual). Everything the farm *does* is an event: produced, spent, earned, observed, reproduced.

`event_category` exists to let each farm label events in its own words (`"huevos"`, `"alimento balanceado"`). Scoped by `(farm_id, type)`, not global.

## Event types

Closed enum. System-defined. User cannot add new types — they add **categories** under existing types.

| type | purpose | required fields | payload tail |
|---|---|---|---|
| `production` | output created by the asset | `quantity`, `unit` | `{}` |
| `expense` | money spent against the asset | `amount`, `currency` | `{ vendor?, invoice_no? }` |
| `income` | money earned from the asset | `amount`, `currency` | `{ buyer?, payment_method? }` |
| `observation` | a recorded fact with no money movement — headcount deltas, health notes, measurements | `quantity`? `unit`? | `{ diagnosis?, treatment?, dose? }` |
| `reproductive` | birth / breeding. Requires `individual_id`. Asset must be `kind=animal`. | — | `{ offspring_count?, outcome? }` |

Enforced by a Pydantic discriminated union on `type`. Wrong-shape payloads are rejected with `422` before reaching the service.

## One user action can be two events

The model separates **money facts** from **inventory facts**. A real-world action often produces both.

| user action | events written |
|---|---|
| Bought 200 chickens for $1500 | `expense` ($1500) + `observation` (quantity `+200`) |
| Sold 20 chickens for $400 | `income` ($400) + `observation` (quantity `-20`) |
| 5 chickens died | `observation` (quantity `-5`) |
| Collected 180 eggs | `production` (quantity `180`, unit `unit`) |
| Vaccinated the flock | `observation` (no quantity, `payload.treatment`) |

The client is responsible for submitting both when a single action implies both. Share an `idempotency_key` prefix across the pair so retries are safe and future tooling can find both halves of a correction (e.g. `sale-<uuid>:income`, `sale-<uuid>:observation`).

## Signed-observation convention

`observation.quantity` is a **signed delta** against the asset's running count.

- `+N` → N units added (births, arrivals, corrections up).
- `-N` → N units removed (deaths, sales, corrections down).
- Omitted → the observation records a non-count fact (health note, measurement). `payload` and `notes` carry the detail.

Absolute recounts ("there are actually 193 right now, I counted") are written as a single observation whose quantity is the delta needed to reach the recounted total, with `payload: { "recount": true }` marking that this event supersedes accumulated drift. UIs can surface recount events differently and reports can ignore non-recount observations within a recount's window if that proves useful — but v1 just sums everything.

Why signed deltas and not two separate columns (`added`, `removed`)? One column means one index, one aggregate, one report query. The sign carries the meaning.

## Current headcount

For an `aggregated` asset:

```sql
SELECT COALESCE(SUM(quantity), 0)
FROM event
WHERE asset_id = :asset_id
  AND type = 'observation'
  AND quantity IS NOT NULL;
```

Served by index `ix_event_asset_type_occurred_at`. No materialized state; always live.

For an `individual` asset, headcount = `COUNT(*)` of individuals with `status='active'` under that `asset_id`. Sales/deaths update the individual's `status`, they don't write observation deltas.

## Reports are live aggregates

No summary tables. No materialized views. No cron jobs rebuilding rollups. Every report endpoint is a SQL aggregate against `event`, hitting an existing index.

- **R1 Profitability per asset** — income minus expense, grouped by `asset_id`, over a date range.
- **R2 Production / headcount over time** — `date_trunc + SUM(quantity)` grouped by bucket, filtered by `type` and `unit`.
- **R3 Cost per produced unit** — R1's expense side ÷ R2's production quantity, per asset.
- **R4 Individual timeline** — raw events for one individual, reverse chronological, paginated.

Trade-off: a very long date range on a very active farm will eventually get slow. When that happens we add a materialized view or hourly rollup *behind the same endpoint* — not before. One source of truth until measured pain says otherwise.

## Service-layer guards

`EventService.create` / `update` assert, in one chokepoint:

1. If `individual_id` set: individual exists, `individual.asset_id == input.asset_id`.
2. If `individual_id` set: asset's `mode == 'individual'`.
3. If `event.type == 'reproductive'`: asset's `kind == 'animal'`.
4. If `category_id` set: category exists, `category.farm_id == input.farm_id`, `category.type == input.type`.
5. All referenced entities (`asset`, `individual`, `category`) belong to the same farm as the event.

Routers never touch models directly. Cross-feature calls go service → service.

## When to reach for what

| I want to record… | where it goes |
|---|---|
| A new kind of thing on the farm | new `asset` (pick `kind` + `mode`) |
| A specific animal with a tag | new `individual` under an `individual`-mode asset |
| A custom label (e.g. "huevos XL") | new `event_category` scoped by `(farm_id, type)` |
| Anything that happened | new `event` |

If you feel tempted to add a new table for a new fact, you probably want a new `event_category` — or, at most, a new key in `event.payload`. Adding tables is a Phase-7+ conversation.
