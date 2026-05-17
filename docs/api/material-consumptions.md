# material-consumptions

_Auto-generated. Do not edit by hand._

## GET /api/v1/farms/{farm_id}/material-consumptions

_List material consumptions in a farm_

**Responses:**
- `200` → Page_MaterialConsumptionRead_ — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/farms/{farm_id}/material-consumptions

_Record a material consumption_

Atomically records the consumption and decrements the material's stock via a paired INVENTORY event. `reason=feeding` requires `consumer_asset_id`; `waste`/`spoilage` must omit it. The consumed `unit` must match a unit the material already holds stock in. Rejects with 409 `insufficient_stock` if stock would go negative. Replaying an `idempotency_key` returns the original record with status 200.

**Request body:**
- `material_asset_id` (integer, required)
- `consumer_asset_id` (integer | null, optional)
- `individual_id` (integer | null, optional)
- `occurred_at` (string (date-time), required)
- `quantity` (number | string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `reason` ('feeding' | 'waste' | 'spoilage', required)
- `notes` (string | null, optional)
- `meta` (object, optional)
- `idempotency_key` (string | null, optional)

**Responses:**
- `201` → MaterialConsumptionRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/material-consumptions/{consumption_id}

_Get one material consumption_

**Responses:**
- `200` → MaterialConsumptionRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## PATCH /api/v1/farms/{farm_id}/material-consumptions/{consumption_id}

_Update a material consumption_

`material_asset_id` is immutable. Changing `quantity`/`unit`/`occurred_at` reconciles the paired inventory event and re-checks stock.

**Request body:**
- `consumer_asset_id` (integer | null, optional)
- `individual_id` (integer | null, optional)
- `occurred_at` (string (date-time) | null, optional)
- `quantity` (number | string | null, optional)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head' | null, optional)
- `reason` ('feeding' | 'waste' | 'spoilage' | null, optional)
- `notes` (string | null, optional)
- `meta` (object | null, optional)

**Responses:**
- `200` → MaterialConsumptionRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## DELETE /api/v1/farms/{farm_id}/material-consumptions/{consumption_id}

_Delete a material consumption_

Hard-deletes the record and reverses its stock effect.

**Responses:**
- `204` → any — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### HTTPValidationError

- `detail` (ValidationError[], optional)

### MaterialConsumptionCreate

- `material_asset_id` (integer, required)
- `consumer_asset_id` (integer | null, optional)
- `individual_id` (integer | null, optional)
- `occurred_at` (string (date-time), required)
- `quantity` (number | string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `reason` ('feeding' | 'waste' | 'spoilage', required)
- `notes` (string | null, optional)
- `meta` (object, optional)
- `idempotency_key` (string | null, optional)

### MaterialConsumptionRead

- `id` (integer, required)
- `farm_id` (integer, required)
- `material_asset_id` (integer, required)
- `consumer_asset_id` (integer | null, required)
- `individual_id` (integer | null, required)
- `inventory_event_id` (integer, required)
- `occurred_at` (string (date-time), required)
- `quantity` (string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `reason` ('feeding' | 'waste' | 'spoilage', required)
- `notes` (string | null, required)
- `meta` (object, required)
- `idempotency_key` (string | null, required)
- `created_by` (integer, required)
- `created_at` (string (date-time), required)
- `updated_at` (string (date-time), required)

### MaterialConsumptionUpdate

- `consumer_asset_id` (integer | null, optional)
- `individual_id` (integer | null, optional)
- `occurred_at` (string (date-time) | null, optional)
- `quantity` (number | string | null, optional)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head' | null, optional)
- `reason` ('feeding' | 'waste' | 'spoilage' | null, optional)
- `notes` (string | null, optional)
- `meta` (object | null, optional)

### PageMeta

- `page` (integer, required)
- `page_size` (integer, required)
- `total` (integer, required)
- `has_next` (boolean, required)

### Page_MaterialConsumptionRead_

- `data` (MaterialConsumptionRead[], required)
- `meta` (PageMeta, required)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

### ConsumptionReason

**Values:** `feeding` | `waste` | `spoilage`

### Unit

**Values:** `g` | `kg` | `lb` | `t` | `ml` | `l` | `gal` | `unit` | `dozen` | `head`

