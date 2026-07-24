# Events & Actions — how it's wired

How assets, events, actions, and reports fit together. Read this before adding
anything that writes an `event` row.

## The model

Three primitives:

- **asset** — anything trackable: an animal flock, a crop field, a **material**
  (feed you buy and consume), a **produce** pool (eggs, milk, a crop yield you
  harvest into and sell), equipment. `kind`
  (`animal`/`crop`/`equipment`/`material`/`produce`/`location`) and `mode`
  (`aggregated` = counted in bulk, `individual` = tagged instances; animals
  only). Material and produce are the two stock-bearing kinds (`INVENTORY_KINDS`);
  both carry inventory balances and are sold via the material-sale action.
- **individual** — one tagged animal; only for `individual`-mode assets.
- **event** — the ledger. One table, discriminated by `type`: `production`,
  `expense`, `income`, `observation`, `reproductive`, `acquisition`,
  `mortality`, `inventory`. Every event belongs to an asset (and a farm). Every
  finance event (`expense`/`income`) carries a `currency_id`.
- **event_category** — a per-farm label for events. A `production` category is
  the farm's notion of a **product** (eggs, milk, a crop): it carries a `unit`
  (required for production categories, forbidden otherwise), and production
  events must be logged in a unit within that product's measurement family
  (`event/guards.py`). Per-asset expected rates live in `asset_production_target`
  (effective-dated; feeds the production-productivity report).

The `event` table is the single source of truth. Stock balances, headcounts,
and every report are *derived* by replaying events — nothing is cached.
Per-farm currency is a first-class resource (`features/currency/`); actions and
`POST /events` resolve it via `CurrencyService.resolve_or_default(farm_id,
currency_id)`, falling back to the farm's preferred currency. Reports never sum
across currencies.

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
| Harvest | `POST .../assets/{id}/harvests` | `production` + `inventory`+ (+ `produce_lot` row) |
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
- **Harvest** is create-only but *does* own a sidecar row: `produce_lot`
  (`harvest/models.py`) holds FKs to its paired `production` + `inventory`
  events and records **which producer** deposited into a shared produce pool. It
  is the link that makes per-producer revenue attribution derivable (the FIFO
  engine reads lots oldest-first). Mirrors the `material_purchase` sidecar;
  `ondelete=RESTRICT` so neither paired event can vanish under it.
- **Table-less actions** (`flock`, `material_sale`) emit events with no owning
  row — correlated only by `payload.source` + `occurred_at`.
- All three are create-only by design (no edit/reverse).
- Each harvest names its destination pool **per request**
  (`HarvestCreate.produce_asset_id`, required), so one producer can feed several
  products and two producers can feed different pools. `asset.produce_asset_id`
  is only a UI default — routing never reads it. The producer→pool link that
  matters is the `produce_lot` row.

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
- `observation` and standalone `expense`·`income` stay manual — no action
  behind them; `reproductive` stays manual too (a failed/offspring-less birth).
  `production` is emitted by the **harvest** action but also stays hand-writable
  via `POST /events` — where it now **requires** a `category_id` (the product /
  production category) so the productivity report can compute produced-vs-expected.
- Inventory mutations go through `event/inventory.py` (`emit_increment` /
  `emit_decrement`, `lock_material`, `assert_non_negative`) — never raw `Event`.

## Reports — derived, never cached

All reports in `report/` aggregate the `event` table (and, for produce
attribution, the `produce_lot` sidecar). Grouped by family under `routes_*`, all
mounted at `/farms/{farm_id}/reports`:

**Money** (`routes_profitability.py`):

- **profitability** — income − expense per **(asset, currency)**. NULL-amount /
  NULL-currency events excluded; currencies never silently summed.
- **profitability-full** — income − total cost (direct expense + average-cost
  feed consumption) per (asset, currency).
- **cost-per-unit** — cost per produced unit per **(producer asset, currency)**.
- **sales-value** — realized average sale price per unit, per asset.
- each of the first three also renders to PDF at `.../pdf`.

**Aggregate** (`routes_aggregate.py`): **aggregate** (generic per-type time
buckets, `group_by=asset` for production/mortality/acquisition) and
**material-consumption-aggregate**.

**Production** (`routes_production.py`): **production-productivity** — produced
vs expected output per (asset, product), where the product is a production
`event_category` and expected comes from an effective-dated `asset_production_target`.

**Produce** (`routes_produce.py`): **produce-outcome** — per (producer, produce
pool) `produced` / `sold` / `lost` / `income_total`, derived by FIFO over
`produce_lot` (never stored).

**Inventory** (`routes_inventory.py`): **inventory-summary** — on-hand balance
per (asset, unit), replayed from the *full* `inventory` history — never
truncated by `date_from`.

**Individual** (`routes_individual.py`): **upcoming-births** and per-individual
**timeline**.

## Adding a new action — checklist

1. New feature folder `features/{name}/` — `router.py`, `actions.py` for
   create-only flows (or `service.py` for full CRUD; either may own a
   `models.py` sidecar table — see `harvest/`), `schemas.py`, `guards.py`.
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
