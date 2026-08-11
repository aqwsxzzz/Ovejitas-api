# Domain Model

Reference doc for the event-sourced core. If the code and this doc disagree, the code wins — open a PR to fix the doc.

Companion to [events-and-actions.md](./events-and-actions.md), [domain-rebuild-plan.md](./domain-rebuild-plan.md) (historical), and [prd_granjas.md](./prd_granjas.md). Inspired by the [farmOS Asset + Log model](https://farmos.org/model/).

## Primitives

The event-sourced core is four tables; everything a farm *does* still resolves to `event` rows.

- **`asset`** — any trackable thing on a farm: animals, crops, equipment, materials, produce pools, locations. Has a `kind` (classifier enum) and, for animals only, a `mode` (`aggregated` for a bulk/count flock, `individual` for tagged instances) and an optional `gestation_days` (20–400). A producer asset may link to a produce pool via `produce_asset_id`. `archived_at` retires it without destroying its history — see [Retiring an asset](#retiring-an-asset-archive-vs-delete).
- **`individual`** — one tagged instance of an `individual`-mode animal asset. Optional. Created only when tracking a specific animal with parentage, tag, birth date, and lifecycle status. Carries FK columns pointing at the events its lifecycle actions emitted (`acquisition_event_id`, `acquisition_expense_event_id`, `mortality_event_id`, `sale_event_id`, `birth_event_id`).
- **`event`** — one immutable fact against an asset (and optionally a specific individual): produced, spent, earned, observed, reproduced, acquired, died, or stock-adjusted.
- **`event_category`** — a per-farm label for events, scoped by `(farm_id, type, name)`. For `production` events a category *is the product* — it carries the product's unit of measure and owns the produce pool holding its stock (`produce_asset_id`, unique). Creating the category provisions the pool, so a product is one thing the farmer creates; `POST /assets` refuses `kind=produce`. Not global.

Beyond the core, several first-class tables carry structured domain state: **`currency`** (per-farm currencies, `features/currency/`), **`asset_production_target`** (expected production rates), and the action sidecars **`material_purchase`**, **`material_consumption`**, **`produce_lot`** (harvest), and **`pregnancy`** — each of which owns the bookkeeping events its action emitted.

## Asset kinds

`AssetKind` (`asset/models.py`) is a closed enum: `animal, crop, equipment, material, produce, location`. Two of these bear stock: `INVENTORY_KINDS = {material, produce}`. `produce` was split out of `material` in #48 — a material is an input you buy and consume (feed), a produce pool is an output you harvest into and sell (eggs, milk, a crop yield).

`mode` is nullable and meaningful only for animals — it is null for material/equipment/location/crop/produce assets.

## Retiring an asset: archive vs delete

An asset has three end states, and only one of them is usually right.

`archived_at` (nullable `timestamptz`) is how a farmer takes an asset out of circulation — a flock sold, a field pulled, a tractor gone. Set it through the normal `PATCH /assets/{id}`, clear it with `null` to bring the asset back. Archiving is always permitted no matter how much history the asset carries, because it destroys nothing. Archived assets are **absent from the default asset list** (`?archived=true` returns them instead) and from `GET /assets/summary`, but still resolve by id so every event, harvest and report that names them keeps reading correctly. Archiving an asset does **not** touch its individuals — they carry their own `status`.

Hard delete is refused once anything records the asset. Six foreign keys point at `asset.id` with `ON DELETE RESTRICT`:

| table | column | what it means |
|---|---|---|
| `produce_lot` | `producer_asset_id` | the asset produced a harvest |
| `produce_lot` | `produce_asset_id` | the pool holds harvested lots |
| `event_category` | `produce_asset_id` | the pool backs a production category |
| `material_consumption` | `consumer_asset_id` | the asset ate a material |
| `material_consumption` | `material_asset_id` | the material was consumed |
| `material_purchase` | `material_asset_id` | the material was purchased |

A seventh path runs through individuals: `pregnancy` holds its individual with RESTRICT, so the CASCADE that clears an asset's individuals is refused too. Events, individuals and production targets cascade away cleanly; `asset.produce_asset_id` is SET NULL.

`asset/deletion.py` declares all seven in one list and both readers use it, so they cannot disagree:

- `AssetService.delete` checks it first and raises `ConflictError` → **409** with a message naming the blocking record ("Cannot delete an asset with recorded harvests"), never a 500. An `IntegrityError` catch sits behind the guard as a backstop.
- `AssetRead.deletable` exposes the same answer, computed for a whole page in one correlated-`EXISTS` query, so a client can hide Delete and offer Retire instead of letting the farmer discover the refusal by clicking. `deletable == true` implies `DELETE` returns 204; `false` implies 409.

Cascade deletion is deliberately not offered: `produce_lot` rows are recorded harvests feeding the productivity report, the pool's stock balance and revenue attribution. Deleting them to satisfy a foreign key would rewrite ledger history.

## Event types

`EventType` (`event/types.py`) is a closed, system-defined enum. Users cannot add types — they add **categories** under existing types.

| type | purpose | required fields | notes |
|---|---|---|---|
| `production` | output created by a producer asset | `category_id`, `quantity`, `unit` | `category_id` is the **product**; `unit` must share a measurement family with the product's unit |
| `expense` | money spent against the asset | `amount` | optional `currency_id` (falls back to farm `default_currency`) |
| `income` | money earned from the asset | `amount` | optional `currency_id` |
| `observation` | a recorded non-money fact — health notes, measurements | — | optional `quantity`/`unit`; detail in `payload`/`notes` |
| `reproductive` | pregnancy/breeding check. Requires `individual_id`, asset `kind=animal` | `individual_id` | backed by the `pregnancy` sidecar |
| `acquisition` | an individual entered the herd | — | **system-only**; emitted by the acquisition action, never via `POST /events` |
| `mortality` | an individual died | — | **system-only**; emitted by the mortality action |
| `inventory` | stock adjustment on a stock-bearing asset | `adjustment`, `quantity`, `unit` | `adjustment` ∈ {`increment`,`decrement`,`reset`}; material/produce assets or aggregated animal flocks only |

Structured detail (vendor, invoice number, buyer, diagnosis, dose, …) lives in the free-form `payload` JSONB — there are no dedicated columns for it. `amount`, `quantity`, `unit`, `adjustment`, and `currency_id` are first-class typed columns.

Enforced by a Pydantic discriminated union on `type` (rejected with `422` before the service) plus DB CHECK constraints `reproductive_requires_individual` and `inventory_requires_adjustment`.

### Units

`unit` is a closed enum (`event/types.py`): `g, kg, lb, t, ml, l, gal, unit, dozen, head`. Units belong to measurement families (count: `unit`/`dozen`; mass; volume; `head`). A production event may be logged in any unit within its product category's family; numeric conversion is the report's concern.

## Domain actions emit their own events

A real-world action that touches both money and inventory is a single server-side **action**, not two client submissions. Each action atomically writes its bookkeeping events inside one transaction and records a sidecar row (where one exists) that owns the paired event FKs. See [events-and-actions.md](./events-and-actions.md) for the full wiring.

| user action | feature | events emitted (server-side) |
|---|---|---|
| Buy material stock | `material_purchase` | `inventory` increment + `expense` |
| Feed / use material | `material_consumption` | `inventory` decrement |
| Sell material or produce | `material_sale` | `inventory` decrement + `income` |
| Acquire an individual | `individual` (acquisition) | `acquisition` (+ `expense` if purchased) |
| Record a death | `individual` (mortality) | `mortality` |
| Sell an individual | `individual` (sale) | `income` |
| Record a birth | `individual` (birth) | `reproductive` + N×`acquisition` |
| Harvest produce | `harvest` | `production` (on producer) + `inventory` increment (on the product's produce pool), recorded as a `produce_lot` |
| Flock acquisition / sale / mortality | `flock` | `inventory` ± with a paired `acquisition`/`income`/`mortality` |
| Pregnancy / ultrasound check | `pregnancy` | `reproductive` |

### Expected due date

A pregnancy check is one row per check, not one row per gestation; current state is
reconstructed latest-record-wins by `report/upcoming_births.py`. A check may record
`service_date` (when she was served) and `sire_individual_id` (who bred her); both are
optional, both are mirrored onto the paired `reproductive` event's payload, and the sire
must be a different individual in the same farm.

`expected_due_at` is derived on **create** when the check is positive and the caller omits
it: `(service_date or occurred_at) + asset.gestation_days`. A value supplied by the caller
is always kept as given, and an asset with no `gestation_days` derives nothing rather than
erroring. PATCH never re-derives, so a stored due date does not move when the flock's
gestation length is edited later.

Clients call the action endpoint; they never assemble the event pair themselves. `idempotency_key` (unique per `(farm_id, key)`) makes the whole action retry-safe. Every finance event carries a `currency_id`, resolved via `CurrencyService.resolve_or_default(farm_id, currency_id)` — reports never sum across currencies.

## Current on-hand / headcount

For a stock-bearing or aggregated asset (material, produce, or an `aggregated` animal flock), on-hand is derived per unit by replaying `inventory` events in `(occurred_at, id)` order — `reset` re-baselines, `increment` adds, `decrement` subtracts:

```python
on_hand = 0
for adjustment, quantity in events:      # type='inventory', one unit
    if adjustment == 'reset':       on_hand  = quantity
    elif adjustment == 'increment': on_hand += quantity
    elif adjustment == 'decrement': on_hand -= quantity
```

Served by the partial index `ix_event_inventory_asset_occurred`. No materialized state; always live. A `decrement` that would drive stock negative is rejected (`InsufficientStockError`). The replay logic lives in `event/inventory.py` and `report/inventory_summary.py`.

For an `individual`-mode asset, headcount = `COUNT(*)` of individuals with `status='active'` under that `asset_id`. Status transitions (`active` → `sold`/`deceased`/`archived`) are driven by lifecycle actions that both update status and emit the corresponding event; they do not write signed deltas.

## Reports are live aggregates

No summary tables. No materialized views. No cron jobs rebuilding rollups. Every report endpoint is a SQL aggregate against `event` (and, for produce attribution, the `produce_lot` sidecar), hitting an existing index. All live under `/farms/{farm_id}/reports`.

- **Profitability (R1)** `/profitability` — income minus expense per (asset, currency).
- **Profitability-full** `/profitability-full` — income minus total cost (direct expense + average-cost feed consumption), per (asset, currency).
- **Cost per unit (R3)** `/cost-per-unit` — cost per produced unit, per (producer asset, currency).
- **Sales value** `/sales-value` — realized average sale price per unit, per asset.
- **Production productivity** `/production-productivity` — produced vs expected output, per (asset, product), against `asset_production_target` (time-weighted, effective-dated rates).
- **Produce outcome** `/produce-outcome` — per-producer contribution to a produce pool and what became of it (derived FIFO attribution, never stored).
- **Inventory summary (R5)** `/inventory-summary` — current on-hand stock per (asset, unit); replays the full inventory history, never truncated by `date_from`.
- **Aggregates** `/aggregate`, `/material-consumption-aggregate` — generic time-bucketed sums.
- **Individual timeline (R4)** `/individuals/{id}/timeline` — paginated events for one individual.
- **Upcoming births** `/upcoming-births` — individuals due within a window.
- PDF variants: `/profitability/pdf`, `/profitability-full/pdf`, `/cost-per-unit/pdf`.

Trade-off: a very long date range on a very active farm will eventually get slow. When that happens we add a materialized view or hourly rollup *behind the same endpoint* — not before.

## Service-layer guards

`EventService.create` / `update` assert, in one chokepoint (`event/guards.py`):

1. If `individual_id` set: individual exists, `individual.asset_id == input.asset_id`.
2. If `individual_id` set: asset's `mode == 'individual'`.
3. If `event.type == 'reproductive'`: asset's `kind == 'animal'`.
4. If `category_id` set: category exists, `category.farm_id == input.farm_id`, `category.type == input.type`.
5. All referenced entities (`asset`, `individual`, `category`, `currency`) belong to the same farm as the event.
6. If `event.type == 'inventory'`: asset is a material/produce kind or an `aggregated` animal.
7. If `event.type == 'production'` and the category has a unit: the event's `unit` shares a measurement family with the product's unit.
8. On update: fields invalid for the event's type are rejected (e.g. `amount` on a production event).

Routers never touch models directly. Cross-feature calls go service → service.

## When to reach for what

| I want to record… | where it goes |
|---|---|
| A new kind of thing on the farm | new `asset` (pick `kind`; set `mode` only for animals) |
| A specific animal with a tag | new `individual` under an `individual`-mode asset |
| A custom label / product (e.g. "huevos XL") | new `event_category` scoped by `(farm_id, type, name)` |
| A real-world action that moves money and/or stock | the action endpoint — it emits the events |
| A plain standalone fact | `POST /events` (expense/income/observation/production) |

Most facts are recorded through a domain **action** (purchase, consumption, sale, acquisition, mortality, birth, harvest, pregnancy), which emits the underlying events for you. Raw `POST /events` is for the plain cases. A custom label is still an `event_category`; for `production` that category is the product. New structured domain state (currencies, production targets, action sidecars) does get its own table when it owns paired events or effective-dated rows.
