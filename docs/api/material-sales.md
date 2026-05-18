# material-sales

_Auto-generated. Do not edit by hand._

## POST /api/v1/farms/{farm_id}/assets/{asset_id}/sales

_Record a material sale_

Sells stock from a `material` asset: decrements the asset's inventory by `quantity` and books a paired INCOME event for `amount` in the farm's default currency. `unit` must match a unit the asset already holds stock in. Rejected with 409 if it would drive stock below zero.

**Request body:**
- `occurred_at` (string (date-time), optional)
- `quantity` (number | string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `amount` (number | string, required)
- `buyer` (string | null, optional)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)

**Responses:**
- `201` → MaterialSaleRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### HTTPValidationError

- `detail` (ValidationError[], optional)

### MaterialSaleCreate

- `occurred_at` (string (date-time), optional)
- `quantity` (number | string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `amount` (number | string, required)
- `buyer` (string | null, optional)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)

### MaterialSaleRead

- `inventory_event_id` (integer, required)
- `income_event_id` (integer, required)
- `on_hand` (string, required)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

### Unit

**Values:** `g` | `kg` | `lb` | `t` | `ml` | `l` | `gal` | `unit` | `dozen` | `head`

