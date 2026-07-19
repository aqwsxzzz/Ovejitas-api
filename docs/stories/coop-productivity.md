# Story — Coop productivity (% of expected laying)

> Origin: farm-owner feedback — *"La productividad de los gallineros? (% cantidad
> sobre puesta de huevos)."*
> Model decided via web research — see [Decisions](#decisions-locked).

## User story

As a farm owner, I want to see each coop's **laying performance over a period** —
actual eggs produced versus what the flock was *expected* to lay — so I can tell
whether a coop is under‑performing.

```
expected eggs   = expected_eggs_per_head_per_day × headcount × days_in_period
productivity %  = eggs produced ÷ expected eggs × 100
```

## What already exists

- **Eggs produced** (the numerator): sum of `PRODUCTION` events (`quantity`,
  `unit`) on the coop asset over the window — already queryable, same shape the
  `cost-per-unit` report uses.
- The coop is an `Asset` (`kind=animal`, `mode=aggregated`).

## What's missing (the gap)

The **denominator has no home**. `Asset` carries no headcount and no expected
laying rate (`asset/models.py`), so "expected eggs" cannot be computed today.

## Decisions (locked)

1. **Per‑head model, not flat per‑coop.** Egg productivity is inherently
   *per‑bird per day* — the industry standard (Hen‑Day Egg Production) divides
   eggs by bird‑days, where 100% = one egg per hen per day. A flat per‑coop
   target breaks the moment flock size changes: a 100‑hen coop set to "80/day"
   reads ~60% after losing 40 birds even though the survivors lay perfectly,
   conflating a *headcount event* with a *rate problem*. Per‑head (`0.8 × 60 ×
   days`) reports ~100% correctly. When the flock is stable the two are
   mathematically identical, so per‑head is never worse.
   ([TNAU layer indices](https://agritech.tnau.ac.in/expert_system/poultry/Layer%20Production%20Indices.html),
   [FAO](https://www.fao.org/4/y4628e/y4628e03.htm))
2. **Headcount: derived from existing flock events, not stored.** The system
   already tracks an aggregated flock's headcount as the live `HEAD` on‑hand of
   its inventory events, maintained by the flock acquisition/sale/mortality
   actions (`features/flock`, read via `on_hand(asset, HEAD)`). A separate
   stored `headcount` column would duplicate that source of truth and silently
   drift from it, so we read the event‑derived count instead. Only the *rate*
   (`expected_eggs_per_head_per_day`) is new and needs persisting.
3. **v1 ignores intra‑period changes.** Productivity uses the coop's *current*
   headcount (`on_hand` as of now) for the whole window. Error is **zero for a
   stable flock** and only appears — growing with the size of the change — when
   birds are added/lost mid‑period. Upgrading later to event‑derived
   **bird‑days** is replaying the same `HEAD` events across the window — no
   schema change.
4. **Presentation: trend, not hard pass/fail.** Show expected‑vs‑actual over the
   period as a trend so normal molt/winter/age dips don't read as failure.
5. **Default rate to pre‑fill: ~0.7 eggs/head/day** (~250 eggs/hen/year — the
   productive end of common backyard dual‑purpose breeds). User‑editable; breed
   alone spans ~2×.
   ([UNH Extension](https://extension.unh.edu/resource/producing-your-own-eggs))

## Acceptance criteria

- The coop `Asset` gains one nullable, editable field:
  `expected_eggs_per_head_per_day` (Decimal). Headcount is **not** stored — it
  is read from the flock's `HEAD` on‑hand.
- `GET /farms/{farm_id}/reports/coop-productivity?date_from=&date_to=` returns one
  row per producing coop: `asset_id`, `asset_name`, `produced`, `expected`,
  `productivity_pct` (or `null`), `missing_capacity`.
- A coop of 10 hens (recorded via flock acquisitions) at 0.8 eggs/head/day over
  10 days that laid 64 eggs reports `expected = 80`, `productivity_pct = 80.0`.
- A coop with `expected_eggs_per_head_per_day` unset **or** a headcount of 0 (no
  flock recorded yet) reports `productivity_pct: null`, `missing_capacity: true`
  — never a divide‑by‑zero (mirrors `has_unvalued_consumption` in the cost
  report).
- Productivity is only defined for egg‑laying coops counted in `unit`/`dozen`;
  rows whose production unit isn't egg‑like are omitted.
- The window obeys the shared whole‑day `date_to` rule (`core/filters.py`).

## Out of scope (v1)

Age / lay‑curve, molt, and seasonal daylight modeling (they swing 30–40%+ and
need hatch dates we don't have); per‑hen tracking; time‑weighted **bird‑days**
(v1 uses current headcount; bird‑days is the deferred, non‑breaking upgrade).
```
