# event-categories

_Auto-generated. Do not edit by hand._

## GET /api/v1/farms/{farm_id}/event-categories

_List event categories in a farm_

**Responses:**
- `200` → Page_EventCategoryRead_ — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/farms/{farm_id}/event-categories

_Create an event category_

`type` is immutable after creation. Uniqueness enforced on (farm, type, name).

**Request body:**
- `type` ('production' | 'expense' | 'income' | 'observation' | 'reproductive' | 'acquisition' | 'mortality' | 'inventory', required)
- `name` (string, required)
- `color` (string | null, optional)

**Responses:**
- `201` → EventCategoryRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/farms/{farm_id}/event-categories/{category_id}

_Get one event category_

**Responses:**
- `200` → EventCategoryRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## PATCH /api/v1/farms/{farm_id}/event-categories/{category_id}

_Update an event category_

Set `archived_at` to archive; set to null to unarchive. `type` cannot change.

**Request body:**
- `name` (string | null, optional)
- `color` (string | null, optional)
- `archived_at` (string (date-time) | null, optional)

**Responses:**
- `200` → EventCategoryRead — Successful Response
- `422` → HTTPValidationError — Validation Error

## DELETE /api/v1/farms/{farm_id}/event-categories/{category_id}

_Delete an event category_

Events referencing this category have their `category_id` set to null.

**Responses:**
- `204` → any — Successful Response
- `422` → HTTPValidationError — Validation Error

## Types

### EventCategoryCreate

- `type` ('production' | 'expense' | 'income' | 'observation' | 'reproductive' | 'acquisition' | 'mortality' | 'inventory', required)
- `name` (string, required)
- `color` (string | null, optional)

### EventCategoryRead

- `id` (integer, required)
- `farm_id` (integer, required)
- `type` ('production' | 'expense' | 'income' | 'observation' | 'reproductive' | 'acquisition' | 'mortality' | 'inventory', required)
- `name` (string, required)
- `color` (string | null, required)
- `archived_at` (string (date-time) | null, required)
- `created_at` (string (date-time), required)
- `updated_at` (string (date-time), required)

### EventCategoryUpdate

- `name` (string | null, optional)
- `color` (string | null, optional)
- `archived_at` (string (date-time) | null, optional)

### HTTPValidationError

- `detail` (ValidationError[], optional)

### PageMeta

- `page` (integer, required)
- `page_size` (integer, required)
- `total` (integer, required)
- `has_next` (boolean, required)

### Page_EventCategoryRead_

- `data` (EventCategoryRead[], required)
- `meta` (PageMeta, required)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

### EventType

**Values:** `production` | `expense` | `income` | `observation` | `reproductive` | `acquisition` | `mortality` | `inventory`

