# Domain Notes

Non-obvious domain knowledge distilled from legacy planning docs (temporal-database-schema.md, animal-tracking-features.md, stories 1.x). The legacy docs described a Node/Sequelize implementation that is being thrown out; these are the *rules and requirements* worth porting. They map onto the new three-primitive model (`production_unit` / `individual` / `event`) described in [domain-rebuild-plan.md](./domain-rebuild-plan.md).

## Feature Roadmap

### Phase 1 — Core foundation
- Historical weight tracking (→ `event` type=`observation`, category=`weight`)
- Basic medical records (→ `event` type=`observation`, category=`vaccination`/`treatment`/`examination`)
- Group / production-unit assignment (→ already in `production_unit`)

### Phase 2 — Extended
- Full breeding management (→ `event` type=`reproductive`)
- Financial tracking per unit / individual (→ `event` type=`expense`/`income`)
- Location history & movement tracking (→ deferred; add `location_event` or reuse `event` with category)
- Vaccination schedules with due-date reminders (→ new concern: see "Deferred concerns" below)

### Phase 3 — Nice-to-have
- Analytics dashboard
- Batch/bulk operations
- Mobile API optimization
- Export / import

## Domain Constraints (enforce in schema or service)

| rule | where | note |
|---|---|---|
| Measurement values must be positive | event service (observation + production) | CHECK on `quantity > 0` is fine for production/observation |
| Temperature must be 35.0–45.0°C | event service (observation payload) | service-level validation, keep in `payload` |
| Gestation period must be 20–400 days | event service (reproductive payload) | sanity bounds |
| Cannot future-date events | event service | `occurred_at <= now()` assertion |
| Events must reference valid, same-farm entities | event guards | already planned — see plan §Service-Layer Guards |
| Currency stored with monetary values | event columns | `amount + currency` required together for income/expense |

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
- **production**: `eggs`, `milk`, `wool`, `meat`, `honey`
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
- **Location as a first-class asset** — for v1, `production_unit.location` is free text. If farmers start moving individuals between real locations and need history, introduce a `location` table and convert movements into events.
- **Vaccination-type catalog** — legacy had a `vaccination_types` lookup table (species-specific recommended frequency). Not in v1; the user models this as `event_category` with notes. Revisit if multi-farm standardization becomes a goal.
- **Weight-unit normalization** — events store `unit` free-text (`kg`, `lbs`). UI converts at display time; DB stores as recorded.

## Porting Map (legacy → new)

| legacy concept | new home |
|---|---|
| `animal_measurements` | `event` (type=`observation`, category=weight/height/…) |
| `animal_health_records` | `event` (type=`observation`, category=vaccination/treatment/…) |
| `animal_locations` | deferred; `event` with location payload, or future `location` table |
| `animal_breeding_events` | `event` (type=`reproductive`) |
| `animal_financial_records` | `event` (type=`expense`/`income`) |
| `animal_group_assignments` | `production_unit` membership (one unit per individual at a time in v1) |
| `vaccination_types` (lookup) | `event_category` (per-farm, user-defined) |
| `farm_locations` (lookup) | deferred; `production_unit.location` text for now |
| `species` / `breed` tables | removed; user writes on `production_unit.name` or `individual.metadata` |
| `animal_summary` materialized view | on-demand report endpoints under `/api/v1/reports` |

## References

- Original PRD: [prd_granjas.md](./prd_granjas.md)
- Implementation plan: [domain-rebuild-plan.md](./domain-rebuild-plan.md)
- farmOS reference model: https://farmos.org/model/
