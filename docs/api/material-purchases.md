# material-purchases

_Auto-generated. Do not edit by hand._

## GET /api/v1/farms/{farm_id}/material-purchases

_List material purchases in a farm_

**Responses:**
- `200` → Page_MaterialPurchaseRead_ — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/farms/{farm_id}/material-purchases

_Record a material purchase_

Atomically records the purchase, increments the material's stock, and books an expense for the amount paid — via a paired INVENTORY and EXPENSE event. The purchased `unit` must match how the material is already tracked (any unit is allowed for a material with no inventory history). Replaying an `idempotency_key` returns the original record with status 200.

**Request body:**
- `material_asset_id` (integer, required)
- `occurred_at` (string (date-time), required)
- `quantity` (number | string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `amount` (number | string, required)
- `supplier` (string | null, optional)
- `notes` (string | null, optional)
- `meta` (object, optional)
- `idempotency_key` (string | null, optional)

**Responses:**
- `201` → MaterialPurchaseRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/material-purchases/{purchase_id}

_Get one material purchase_

**Responses:**
- `200` → MaterialPurchaseRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## PATCH /api/v1/farms/{farm_id}/material-purchases/{purchase_id}

_Update a material purchase_

`material_asset_id` is immutable. Changing `quantity`/`unit`/`occurred_at` reconciles the inventory event; `amount`/`occurred_at` reconciles the expense. An edit that would drive stock negative is rejected with 409.

**Request body:**
- `occurred_at` (string (date-time) | null, optional)
- `quantity` (number | string | null, optional)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head' | null, optional)
- `amount` (number | string | null, optional)
- `supplier` (string | null, optional)
- `notes` (string | null, optional)
- `meta` (object | null, optional)

**Responses:**
- `200` → MaterialPurchaseRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## DELETE /api/v1/farms/{farm_id}/material-purchases/{purchase_id}

_Delete a material purchase_

Hard-deletes the record and reverses both the stock increment and the expense. Rejected with 409 if reversing the stock would go negative.

**Responses:**
- `204` → any — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### HTTPValidationError

- `detail` (ValidationError[], optional)

### MaterialPurchaseCreate

- `material_asset_id` (integer, required)
- `occurred_at` (string (date-time), required)
- `quantity` (number | string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `amount` (number | string, required)
- `supplier` (string | null, optional)
- `notes` (string | null, optional)
- `meta` (object, optional)
- `idempotency_key` (string | null, optional)

### MaterialPurchaseRead

- `id` (integer, required)
- `farm_id` (integer, required)
- `material_asset_id` (integer, required)
- `inventory_event_id` (integer, required)
- `expense_event_id` (integer, required)
- `occurred_at` (string (date-time), required)
- `quantity` (string, required)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head', required)
- `amount` (string, required)
- `currency` (string, required)
- `supplier` (string | null, required)
- `notes` (string | null, required)
- `meta` (object, required)
- `idempotency_key` (string | null, required)
- `created_by` (integer, required)
- `created_at` (string (date-time), required)
- `updated_at` (string (date-time), required)

### MaterialPurchaseUpdate

- `occurred_at` (string (date-time) | null, optional)
- `quantity` (number | string | null, optional)
- `unit` ('g' | 'kg' | 'lb' | 't' | 'ml' | 'l' | 'gal' | 'unit' | 'dozen' | 'head' | null, optional)
- `amount` (number | string | null, optional)
- `supplier` (string | null, optional)
- `notes` (string | null, optional)
- `meta` (object | null, optional)

### PageMeta

- `page` (integer, required)
- `page_size` (integer, required)
- `total` (integer, required)
- `has_next` (boolean, required)

### Page_MaterialPurchaseRead_

- `data` (MaterialPurchaseRead[], required)
- `meta` (PageMeta, required)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

### Unit

**Values:** `g` | `kg` | `lb` | `t` | `ml` | `l` | `gal` | `unit` | `dozen` | `head`

