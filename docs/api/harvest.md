# harvest

_Auto-generated. Do not edit by hand._

## POST /api/v1/farms/{farm_id}/assets/{asset_id}/harvests

_Record a harvest_

Collects produce from an `animal` or `crop` asset: emits a PRODUCTION event on the source asset and an INVENTORY increment on the produce asset linked via the source's `produce_asset_id`. `quantity` and `unit` feed both events; `unit` must match the produce asset's existing stock unit. The source asset must have a produce asset linked.

**Request body:**
- `occurred_at` (string (date-time), optional)
- `quantity` (number | string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)

**Responses:**
- `201` → HarvestRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### HTTPValidationError

- `detail` (ValidationError[], optional)

### HarvestCreate

- `occurred_at` (string (date-time), optional)
- `quantity` (number | string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `category_id` (integer | null, optional)
- `notes` (string | null, optional)

### HarvestRead

- `production_event_id` (integer, required)
- `inventory_event_id` (integer, required)
- `produce_balance` (string, required)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

### Unit

**Values:** `g` | `kg` | `lb` | `t` | `ml` | `l` | `gal` | `unit` | `dozen` | `head`

