# Story — Egg value & profit from egg sales

> Origin: farm-owner feedback — *"Registrar profit por venta de huevos
> (producción), cómo se refleja el valor del huevo?"*

## User story

As a farm owner, I want each egg sale to record **how much an egg is worth**, so
the app can show the value of what I produced and the profit per coop — not just
a lump sum of income.

## What already exists

- A sale (`POST /farms/{farm_id}/material-sales`) writes one `INCOME` event with
  a **total `amount`** and decrements egg inventory — atomically
  (`material_sale/actions.py`).
- `PRODUCTION`/harvest events carry **quantity only, no money**
  (`event/schemas.py`).

## What's missing (the gap)

There is **no per‑unit value** anywhere. The egg's worth is only *implicit* as
`amount ÷ quantity` at sale time, and produced‑but‑unsold eggs carry no value at
all. So "el valor del huevo" can't be surfaced today.

## Decisions needed before building

1. **Derive vs. store the unit price.** Recommended MVP: **derive** it — no
   schema change. Average sale price over a period =
   `Σ income.amount ÷ Σ eggs sold`, per coop and currency. Cheap, honest, good
   enough to answer the question. (Alternative: add an explicit `unit_price` to
   the sale payload if owners want to set it directly — defer until asked.)
2. **Profit vs. revenue.** "Profit por venta" = sale income − cost of those eggs.
   The cost basis already exists as `cost-per-unit` (direct expense + valued
   feed). Profit per coop = `avg_sale_price − cost_per_unit`, per produced unit.
3. **Inventory valuation (COGS).** Valuing unsold egg stock on the balance sheet
   is a bigger model change — **out of scope** for this story.

## Acceptance criteria

- `GET /farms/{farm_id}/reports/egg-value?date_from=&date_to=` (or an extension of
  the profitability report) returns, per coop + currency: `eggs_sold`,
  `income_total`, `avg_unit_value` (`income ÷ eggs_sold`), and — when a
  `cost_per_unit` is available — `unit_profit`.
- Selling 24 eggs for 240 ARS reports `avg_unit_value = 10.00 ARS`.
- A coop that produced eggs but sold none reports `avg_unit_value: null` (no
  divide‑by‑zero), not `0`.
- Currencies are never mixed (same rule as the profitability report).

## Out of scope

Explicit per‑sale unit price entry, inventory/COGS valuation of unsold stock,
FIFO/weighted‑average cost layers.
```
