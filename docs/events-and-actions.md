# Events & Actions — how it's wired

How assets, events, actions, and reports fit together. Read this before adding
anything that writes an `event` row.

## The model

Three primitives:

- **asset** — anything trackable: an animal flock, a crop field, a material
  (feed, eggs), equipment. `kind` (animal/crop/equipment/material/location) and
  `mode` (`aggregated` = counted in bulk, `individual` = tagged instances).
- **individual** — one tagged animal; only for `individual`-mode assets.
- **event** — the ledger. One table, discriminated by `type`: `production`,
  `expense`, `income`, `observation`, `reproductive`, `acquisition`,
  `mortality`, `inventory`. Every event belongs to an asset (and a farm).

The `event` table is the single source of truth. Stock balances, headcounts,
and every report are *derived* by replaying events — nothing is cached.

## Philosophy 1 — actions emit events

A real-world act is recorded as one **action** whose service **atomically emits
the corresponding event row(s)** in the same transaction. Users never
hand-write an event where an action exists. Events are a trustworthy derived
ledger, not manual input.

The 11 actions and what each emits (all in one transaction, rollback on failure):

| Action | Endpoint | Emits |
|---|---|---|
| Individual create | `POST .../individuals` | `acquisition` (+ `expense` if purchased) |
| Individual → deceased | `PATCH .../individuals/{id}` | `mortality` |
| Individual → sold | `PATCH .../individuals/{id}` | `income` |
| Birth | `POST .../individuals/{id}/births` | `reproductive` + N×`acquisition` |
| Flock acquisition | `POST .../assets/{id}/flock/acquisitions` | `inventory`+ + `acquisition` (+ `expense`) |
| Flock sale | `POST .../assets/{id}/flock/sales` | `inventory`− + `income` |
| Flock mortality | `POST .../assets/{id}/flock/mortalities` | `inventory`− + `mortality` |
| Harvest | `POST .../assets/{id}/harvests` | `production` + `inventory`+ |
| Material purchase | `POST .../material-purchases` | `inventory`+ + `expense` |
| Material consumption | `POST .../material-consumptions` | `inventory`− |
| Material sale | `POST .../assets/{id}/sales` | `inventory`− + `income` |

Every action-emitted event carries `payload.source` (e.g. `"flock_acquisition"`,
`"harvest"`) identifying which action produced it.

## Linkage

- **Individuals** carry FK columns back to their lifecycle events
  (`acquisition_event_id`, `mortality_event_id`, `sale_event_id`,
  `birth_event_id`). The individual service is the single writer.
- **Table-backed actions** (`material_purchase`, `material_consumption`) own a
  row that holds FKs to their paired events.
- **Table-less actions** (`flock`, `harvest`, `material_sale`) emit events with
  no owning row — correlated only by `payload.source` + `occurred_at`. They are
  create-only by design (no edit/reverse).
- Harvest links a producer asset to its produce asset via
  `asset.produce_asset_id`.

## Event write paths — the rules

`POST /events` and the action endpoints both create events, but the action
layer owns invariants the generic endpoint must respect:

- **Action-owned events** (any event with `payload.source` set) **cannot be
  edited or deleted** via `PATCH`/`DELETE /events` — go through the action.
  `payload.source` is reserved: a manual `POST /events` may not set it.
- **`inventory` events stay hand-writable** via `POST /events` (a stocktake
  `reset` has no action behind it) — but a manual decrement runs the same
  `SELECT FOR UPDATE` lock + negative-stock guard as the action layer.
- `acquisition` / `mortality` are **not** in the `EventCreate` union — they are
  action-only.
- `production` / `observation` / standalone `expense`·`income` stay manual:
  there is no action behind them. `reproductive` stays manual too (a
  failed/offspring-less birth).
- Inventory mutations go through `event/inventory.py` (`emit_increment` /
  `emit_decrement`, `lock_material`, `assert_non_negative`) — never raw `Event`.

## Reports — derived, never cached

All reports in `report/` aggregate the `event` table:

- **profitability** — income − expense per asset.
- **aggregate** — generic per-type time buckets (`group_by=asset` for
  production / mortality / acquisition).
- **cost-per-unit** — cost per produced unit per producer asset (direct
  expenses + average-cost-valued feed consumption ÷ production).
- **inventory-summary** — on-hand balance per (asset, unit), replayed from
  `inventory` events. Balance replays the *full* history — never truncate it
  by `date_from`.

## Adding a new action — checklist

1. New feature folder `features/{name}/` — `router.py`, `actions.py` (or a
   `service.py` if it owns a table), `schemas.py`, `guards.py`.
2. The action validates, then emits its events in **one** `try/commit/except
   rollback` block. Reuse `emit_increment`/`emit_decrement` for stock; build
   `expense`/`income`/`mortality` events inline (see `flock/actions.py`).
3. Tag every emitted event with a unique `payload.source`.
4. If it mutates stock, the asset must pass `validate_type_against_asset`.
5. Register the router in `main.py`.
6. Integration tests with a real DB; mirror an existing action's test file.
7. `docker compose exec app uv run pytest && ruff check && mypy src` — all green.

## Conventions

- Feature-folder layout; the service/action is the only layer touching the DB.
- Files stay under 200 lines — split before crossing.
- Run everything in Docker: `docker compose exec app uv run <cmd>`.
- See `CLAUDE.md` for the full project rules.
