# Story — Coop productivity (% of expected laying)

> Origin: farm-owner feedback — *"La productividad de los gallineros? (% cantidad
> sobre puesta de huevos)."*

## User story

As a farm owner, I want to see each coop's **productivity for a period** —
actual eggs produced as a percentage of what the flock was *expected* to lay — so
I can tell at a glance whether a coop is under‑performing.

```
productivity % = eggs produced in period
                 ─────────────────────────────────  × 100
                 hen_count × expected_eggs_per_hen_per_day × days_in_period
```

## What already exists

- **Eggs produced** is the numerator: sum of `PRODUCTION` events (`quantity`,
  `unit`) on the coop asset over the window — already queryable, same shape the
  `cost-per-unit` report uses.
- The coop is an `Asset` (`kind=animal`, `mode=aggregated`).

## What's missing (the gap)

The **denominator has no home**. `Asset` carries no headcount and no expected
laying rate (`asset/models.py`), so "expected eggs" cannot be computed today.

## Decisions needed before building

1. **Where does expected laying live?** Recommended MVP: two nullable fields on
   the animal asset — `head_count` (int) and `expected_daily_rate` (Decimal,
   eggs per head per day). Simple, explicit, editable. (Alternative: derive
   `head_count` from acquisition/mortality events — heavier, defer.)
2. **Unit handling.** Productivity is only defined for egg‑laying coops counted
   in `unit`/`dozen`. Rows whose production unit isn't egg‑like are omitted.
3. **Empty denominator.** If `head_count` or `expected_daily_rate` is unset,
   return `productivity_pct: null` and a `missing_capacity: true` flag rather
   than guessing — mirrors how `cost-per-unit` surfaces `has_unvalued_consumption`.

## Acceptance criteria

- `GET /farms/{farm_id}/reports/coop-productivity?date_from=&date_to=` returns one
  row per producing coop: `asset_id`, `asset_name`, `produced`, `expected`,
  `productivity_pct` (or `null`), `missing_capacity`.
- A coop of 10 hens at 0.8 eggs/head/day over 10 days that laid 64 eggs reports
  `expected = 80`, `productivity_pct = 80.0`.
- A coop with no capacity configured reports `productivity_pct: null`,
  `missing_capacity: true`, never a divide‑by‑zero.
- The date window obeys the shared whole‑day `date_to` rule (see
  `core/filters.py`).

## Out of scope

Per‑hen tracking, automatic headcount from events, breed‑specific lay curves.
```
