# Domain Notes

Non-obvious domain knowledge distilled from legacy planning docs (temporal-database-schema.md, animal-tracking-features.md, stories 1.x). The legacy docs described a Node/Sequelize implementation that was thrown out; these are the *rules and requirements* worth porting. They map onto the event-sourced core (`asset` / `individual` / `event` / `event_category`) described in [domain-model.md](./domain-model.md).

> **Note (2026):** the rebuild is shipped and the schema has evolved well past the original plan. For the current model read [domain-model.md](./domain-model.md) and the feature models under `src/ovejitas/features/*/models.py`. System event types are now eight — `production, expense, income, observation, reproductive, acquisition, mortality, inventory` — the last three emitted by domain actions (acquisition/mortality flows, inventory movements), not hand-entered. This file is kept for the underlying *requirements*, most of which still hold.

## Feature Roadmap (mostly delivered)

### Phase 1 — Core foundation — SHIPPED
- Historical weight tracking (→ `event` type=`observation`, category=`weight`)
- Basic medical records (→ `event` type=`observation`, category=`vaccination`/`treatment`/`examination`)
- Group / asset assignment (→ `asset`)

### Phase 2 — Extended — mostly SHIPPED
- Full breeding management (→ `event` type=`reproductive`; `pregnancy` action) — SHIPPED
- Financial tracking per unit / individual (→ `event` type=`expense`/`income`) — SHIPPED
- Location containment — SHIPPED as current state (`asset.location_asset_id` → a `location` asset). Movement *history* still deferred: when it lands it is a move action emitting its own event, with this column kept as the current-state projection.
- Vaccination schedules with due-date reminders — still deferred (see "Deferred concerns")

### Phase 3 — Nice-to-have — partly SHIPPED
- Analytics dashboard (→ the `report` suite delivers the aggregates) — partly SHIPPED
- Batch/bulk operations
- Mobile API optimization
- Export / import (→ report PDF export exists)

## Domain Constraints (enforce in schema or service)

| rule | where | note |
|---|---|---|
| Measurement values must be positive | event service (observation + production) | CHECK on `quantity > 0` is fine for production/observation |
| Temperature must be 35.0–45.0°C | event service (observation payload) | service-level validation, keep in `payload` |
| Gestation period must be 20–400 days | `asset.gestation_days` — Pydantic bound + `ck_asset_gestation_days_sane` | SHIPPED; animal assets only, and the base for deriving a check's `expected_due_at` |
| Cannot future-date events | event service | `occurred_at <= now()` assertion |
| Events must reference valid, same-farm entities | event guards | already planned — see plan §Service-Layer Guards |
| Currency stored with monetary values | `currency` table + `event.currency_id` FK | Currency is a first-class per-farm resource (feature: `currency`); `amount` + `currency_id` resolved together for expense/income (falls back to the farm default) |

## Non-Obvious Requirements

- **Point-in-time queries** — "what was the animal's weight on 2025-06-01?". The event table with `(individual_id, occurred_at DESC)` index supports this natively: `WHERE individual_id=? AND occurred_at <= ? ORDER BY occurred_at DESC LIMIT 1`.
- **Measurement method** — weight can come from `scale`, `tape`, or `visual_estimate`. Store in `payload.method`, not a column. Different accuracy; relevant when charting.
- **Upcoming vaccinations / due-date queries** — vaccination events carry a `next_due_date` in `payload`. A report/endpoint must answer "what's due in the next 30 days per farm". Index on `(farm_id, (payload->>'next_due_date')::date)` if this proves slow.
- **Attachments** — medical/financial records reference files (images, invoices). `payload.attachments` is a JSON array of file refs. File storage itself is out of scope for v1.
- **Veterinarian name** — free-text field on observation events; not a FK. Goes in `payload.veterinarian`.
- **Offline sync capability** — mobile farmers record events without network. Addressed by `event.idempotency_key` (already in schema) + timestamp-based replay on reconnect.
- **Last-measurement convenience** — UI often wants "current weight" without scanning history. Either compute on read (`LATERAL` subquery) or denormalize onto `individual.current_weight` via trigger. Defer the denormalization until perf requires it.
- **Partner info for breeding** — the other parent may be an external animal (e.g. AI semen). Store free-form `payload.partner_external` when there's no `father_id`.
- **Multiple offspring per birth** — `payload.offspring_count`. If the app later needs to track each offspring individually, spawn new `individual` rows with `mother_id`/`father_id` set.

## Taxonomies (user-supplied, via event_category)

These were hard-coded enums in the legacy schema. In the new model they are **user-defined categories** per farm, scoped by event type. Seed suggestions for onboarding:

- **observation (was health)**: `weight`, `height`, `body_condition`, `vaccination`, `treatment`, `examination`, `illness`, `injury`
- **production**: `eggs`, `milk`, `wool`, `meat`, `honey` — production categories are the farm's *products*: each carries a unit of measure (`event_category.unit`) and can own per-asset expected-rate targets (`asset_production_target`). The former egg-specific model was retired in favor of this generic product.
- **expense**: `feed`, `medication`, `veterinary`, `acquisition`, `maintenance`, `insurance`
- **income**: `animal_sale`, `product_sale`, `breeding_fee`
- **reproductive**: `breeding`, `ai_breeding`, `pregnancy_check`, `birth`, `weaning`

## Success Metrics (product-level, not backend-level)

- 50% reduction in time spent on record-keeping.
- Measurable health-outcome improvement within 6 months.
- Clear ROI visibility per unit or individual.
- Breeding decisions driven by recorded data, not memory.

## Deferred Concerns

These legacy features are *not* in v1 scope but the schema should not preclude them:

- **Scheduled reminders** (vaccination due dates) — requires a notification system (email/push) + background jobs. Plan says "no background jobs in v1". Data model already supports the query (`next_due_date` in payload). Add ARQ + a daily job when this becomes real.
- **Materialized views for analytics** — legacy plan suggested `animal_summary`. Skip until a report actually hurts.
- **Partitioning** by date — premature; revisit when `event` table hits tens of millions of rows.
- **Movement history** — containment itself is settled: `asset.location_asset_id` points at a `location` asset, the free-text `location` string is gone, and nesting works. What is *not* built is history — the location of an asset at a past date. When a farmer needs it, add a move action that emits a movement event and keeps `location_asset_id` as the current-state projection; no separate `location` table, since a location is already an asset kind.
- **Vaccination-type catalog** — legacy had a `vaccination_types` lookup table (species-specific recommended frequency). Not in v1; the user models this as `event_category` with notes. Revisit if multi-farm standardization becomes a goal.
- **Weight-unit normalization** — `unit` is a closed enum (`Unit`: g/kg/lb/t/ml/l/gal/unit/dozen/head) shared across events, categories, and material/produce rows. UI converts at display time; DB stores the enum value as recorded.

## Porting Map (legacy → new)

| legacy concept | new home |
|---|---|
| `animal_measurements` | `event` (type=`observation`, category=weight/height/…) |
| `animal_health_records` | `event` (type=`observation`, category=vaccination/treatment/…) |
| `animal_locations` | deferred; `event` with location payload, or future `location` table |
| `animal_breeding_events` | `event` (type=`reproductive`) |
| `animal_financial_records` | `event` (type=`expense`/`income`) |
| `animal_group_assignments` | `asset` membership (one unit per individual at a time in v1) |
| `vaccination_types` (lookup) | `event_category` (per-farm, user-defined) |
| `farm_locations` (lookup) | deferred; `asset.location` text for now |
| `species` / `breed` tables | removed; user writes on `asset.name` or `individual.metadata` |
| `animal_summary` materialized view | on-demand report endpoints under `/api/v1/reports` |

## References

- Original PRD: [prd_granjas.md](./prd_granjas.md)
- Implementation plan: [domain-rebuild-plan.md](./domain-rebuild-plan.md)
- farmOS reference model: https://farmos.org/model/
