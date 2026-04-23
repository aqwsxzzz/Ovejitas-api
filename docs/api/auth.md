# auth

_Auto-generated. Do not edit by hand._

## POST /api/v1/auth/register

_Register a new user_

Creates a user, a default 'My Farm' (USD), and an owner membership in one transaction. Returns an access + refresh token pair.

**Request body:**
- `email` (string (email), required)
- `name` (string, required)
- `password` (string, required)

**Responses:**
- `201` → TokenPair — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/auth/login

_Exchange credentials for tokens_

Returns 401 on unknown email or wrong password (no user enumeration).

**Request body:**
- `email` (string (email), required)
- `password` (string, required)

**Responses:**
- `200` → TokenPair — Successful Response
- `422` → HTTPValidationError — Validation Error

## POST /api/v1/auth/refresh

_Exchange a refresh token for a new token pair_

**Request body:**
- `refresh_token` (string, required)

**Responses:**
- `200` → TokenPair — Successful Response
- `422` → HTTPValidationError — Validation Error

## GET /api/v1/auth/me

_Current user and farm memberships_

**Responses:**
- `200` → MeResponse — Successful Response

## Types

### FarmMembershipRead

- `farm_id` (integer, required)
- `role` (string, required)

### HTTPValidationError

- `detail` (ValidationError[], optional)

### LoginInput

- `email` (string (email), required)
- `password` (string, required)

### MeResponse

- `user` (UserRead, required)
- `memberships` (FarmMembershipRead[], required)

### RefreshInput

- `refresh_token` (string, required)

### RegisterInput

- `email` (string (email), required)
- `name` (string, required)
- `password` (string, required)

### TokenPair

- `access_token` (string, required)
- `refresh_token` (string, required)
- `token_type` (string, optional)

### UserRead

- `id` (integer, required)
- `email` (string (email), required)
- `name` (string, required)
- `created_at` (string (date-time), required)

### ValidationError

- `loc` (string | integer[], required)
- `msg` (string, required)
- `type` (string, required)
- `input` (any, optional)
- `ctx` (object, optional)

