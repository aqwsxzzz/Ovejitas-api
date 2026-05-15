# reports

_Auto-generated. Do not edit by hand._

## GET /api/v1/farms/{farm_id}/reports/profitability

_R1 — income minus expense per asset_

One row per (asset, currency). Events with NULL amount/currency are excluded. Different currencies are never silently summed.

**Responses:**
- `200` → ProfitabilityReport — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/reports/aggregate

_Generic time-bucketed aggregate over events of one type_

Dispatches on `type` and returns uniform `{bucket, group, group_label, measure, value, asset_id}` rows.

- production / observation: SUM(quantity) grouped by unit
- mortality / acquisition: SUM(quantity) as headcount, no grouping
- inventory: net flow within window (increments minus decrements).   Pass `adjustment=reset|increment|decrement` to isolate one kind.
- expense / income: SUM(amount) grouped by currency
- reproductive: COUNT(*) of events

Filters `unit`, `adjustment`, `currency` are ignored for types where they do not apply.

**`group_by=asset`** breaks rows down per asset. Each row then carries a stable `group` key (the asset id as a string), a `group_label` (the asset name), and an `asset_id`. When `group_by` is omitted, rows are unchanged: `group_label` and `asset_id` stay `null`.

Compatibility matrix — `type` vs `group_by`:

| type | group_by=asset |
| --- | --- |
| mortality | supported |
| acquisition | supported |
| production / observation / inventory / expense / income / reproductive | rejected with 422 |

**Responses:**
- `200` → AggregateReport — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/reports/cost-per-unit

_R3 — expense total ÷ produced quantity, per asset_

Requires `unit` (what counts as one produced unit). One row per (asset, currency). Assets without BOTH production (in the given unit) and expense events are omitted — a currency cannot be inferred without an expense row. The expense total is not unit-filtered: all of the asset's expenses are attributed to the queried production unit, so this number is only meaningful for single-output assets.

**Responses:**
- `200` → CostPerUnitReport — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/reports/profitability/pdf

_R1 — PDF download_

**Responses:**
- `200` → any — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/reports/cost-per-unit/pdf

_R3 — PDF download_

**Responses:**
- `200` → any — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/reports/inventory-summary

_R5 — current on-hand inventory across material assets_

One row per (material asset, unit). On-hand is derived from INVENTORY events: sum of increments minus decrements since the most recent reset. Date filters bound the events considered, not the resulting balance.

**Responses:**
- `200` → InventorySummaryReport — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/reports/individuals/{individual_id}/timeline

_R4 — paginated event timeline for one individual_

**Responses:**
- `200` → Page_EventRead_ — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### AggregateMeta

- `type` ('production' | 'expense' | 'income' | 'observation' | 'reproductive' | 'acquisition' | 'mortality' | 'inventory', required)
- `measure` ('sum_quantity' | 'sum_amount' | 'count', required)
- `bucket` ('day' | 'week' | 'month', required)
- `group_key` (string | null, required)
- `group_by` ('asset' | null, optional)

### AggregateReport

- `data` (AggregateRow[], required)
- `meta` (AggregateMeta, required)

### AggregateRow

- `bucket` (string (date-time), required)
- `group` (string | null, required)
- `group_label` (string | null, optional)
- `measure` ('sum_quantity' | 'sum_amount' | 'count', required)
- `value` (string, required)
- `asset_id` (integer | null, optional)

### CostPerUnitReport

- `data` (CostPerUnitRow[], required)
- `totals` (CostPerUnitTotal[], required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)

### CostPerUnitRow

- `asset_id` (integer, required)
- `asset_name` (string, required)
- `currency` (string, required)
- `quantity` (string, required)
- `expense_total` (string, required)
- `cost_per_unit` (string, required)

### CostPerUnitTotal

- `currency` (string, required)
- `quantity` (string, required)
- `expense_total` (string, required)
- `cost_per_unit` (string, required)

### EventRead

- `id` (integer, required)
- `farm_id` (integer, required)
- `asset_id` (integer, required)
- `individual_id` (integer | null, required)
- `type` ('production' | 'expense' | 'income' | 'observation' | 'reproductive' | 'acquisition' | 'mortality' | 'inventory', required)
- `category_id` (integer | null, required)
- `occurred_at` (string (date-time), required)
- `quantity` (string | null, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head' | null, required)
- `amount` (string | null, required)
- `currency` (string | null, required)
- `adjustment` ('increment' | 'decrement' | 'reset' | null, required)
- `notes` (string | null, required)
- `payload` (object, required)
- `idempotency_key` (string | null, required)
- `created_by` (integer, required)
- `created_at` (string (date-time), required)
- `updated_at` (string (date-time), required)

### HTTPValidationError

- `detail` (ValidationError[], optional)

### InventorySummaryReport

- `data` (InventorySummaryRow[], required)

### InventorySummaryRow

- `asset_id` (integer, required)
- `asset_name` (string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `on_hand` (string, required)

### PageMeta

- `page` (integer, required)
- `page_size` (integer, required)
- `total` (integer, required)
- `has_next` (boolean, required)

### Page_EventRead_

- `data` (EventRead[], required)
- `meta` (PageMeta, required)

### ProfitabilityReport

- `data` (ProfitabilityRow[], required)
- `totals` (ProfitabilityTotal[], required)

### ProfitabilityRow

- `asset_id` (integer, required)
- `asset_name` (string, required)
- `currency` (string, required)
- `income_total` (string, required)
- `expense_total` (string, required)
- `net` (string, required)

### ProfitabilityTotal

- `currency` (string, required)
- `income_total` (string, required)
- `expense_total` (string, required)
- `net` (string, required)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

### AggregateMeasure

**Values:** `sum_quantity` | `sum_amount` | `count`

### Bucket

**Values:** `day` | `week` | `month`

### EventType

**Values:** `production` | `expense` | `income` | `observation` | `reproductive` | `acquisition` | `mortality` | `inventory`

### GroupBy

**Values:** `asset`

### InventoryAdjustment

**Values:** `increment` | `decrement` | `reset`

### Unit

**Values:** `g` | `kg` | `lb` | `t` | `ml` | `l` | `gal` | `unit` | `dozen` | `head`

