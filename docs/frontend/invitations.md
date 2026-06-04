# Frontend Guide — Farm Invitations

How to wire the invitation feature into the UI. The API contract (paths,
schemas) lives in [`docs/api/invitations.yaml`](../api/invitations.yaml); this
doc covers the **flow** and the decisions the frontend owns.

All paths are under `/api/v1`. Authenticated calls send `Authorization: Bearer <access_token>`.

---

## Concept

An invite is **email-bound, single-use, and expires in 7 days**. The flow has
two sides:

- **Inviter** (a farm `owner` or `admin`) generates a link and shares it manually
  (WhatsApp, email, etc. — the API does **not** send email).
- **Recipient** opens the link and joins the farm. They may already have an
  account, or be brand new — the server decides which, the frontend just renders
  the matching form.

---

## Inviter side

### 1. Create an invite

```
POST /api/v1/farms/{farm_id}/invitations
Authorization: Bearer <token>            # must be owner/admin of the farm
{ "email": "person@example.com", "role": "member" }   # role: "admin" | "member"
```

Response `201`:

```json
{
  "invitation": { "id": 12, "farm_id": 3, "email": "person@example.com",
                  "role": "member", "status": "pending",
                  "expires_at": "2026-06-09T15:00:00Z", "created_at": "..." },
  "token": "x7Hq...long-opaque-string"
}
```

> **The `token` is returned exactly once.** Build the shareable link on the
> frontend — e.g. `https://app.example.com/invite?token=<token>` — and show it to
> the inviter to copy. It cannot be retrieved again; if lost, revoke and re-create.

`role: "owner"` is rejected (`422`).

### 2. List invites

```
GET /api/v1/farms/{farm_id}/invitations?status=pending&sort=-created_at&page=1&page_size=20
```

Returns the standard `Page` envelope (`{ data: InvitationRead[], meta: {...} }`).
`status` filter is optional (`pending` | `accepted` | `revoked`). Note the list
does **not** include the token — only its metadata.

### 3. Revoke a pending invite

```
POST /api/v1/farms/{farm_id}/invitations/{invitation_id}/revoke   →  204
```

---

## Recipient side

The recipient lands on your `/invite?token=...` page. Two API calls: **resolve**
(to decide the form), then **accept**.

### 1. Resolve the token → pick the form

```
GET /api/v1/invitations/{token}          # public, no auth
```

Response `200`:

```json
{ "farm_id": 3, "farm_name": "Green Pastures", "role": "member",
  "email": "person@example.com", "requires_registration": true }
```

Use the response to render the screen:

- Show `"You've been invited to join <farm_name> as <role>."`
- The email is fixed by the invite — display it read-only, don't let the user change it.
- Branch on **`requires_registration`**:
  - `true`  → show **name + password** fields (new account).
  - `false` → show **password only** (existing account; they re-enter their password).

`requires_registration` is the *only* thing that decides the form. Do not put any
"does this user exist" logic in the frontend — the server already answered.

### 2. Accept

Same endpoint for both cases; send what the form collected:

```
POST /api/v1/invitations/{token}/accept   # public, no auth
# new user:      { "password": "...", "name": "Their Name" }
# existing user: { "password": "..." }
```

Response `200` is a **token pair** — the user is now logged in:

```json
{ "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### 3. After accept

1. Store the returned `access_token` / `refresh_token` exactly as you do after login.
2. Call `GET /api/v1/auth/me` — the response `memberships[]` now includes the farm
   they just joined.
3. Set the active farm to the invited `farm_id` and route into the app.

A brand-new invitee has **only** the invited farm in `memberships` (no personal
"My Farm"). An existing user has their own farm(s) **plus** the invited one — this
is what powers the farm switcher.

---

## Error handling

The server is authoritative; the frontend re-checks at accept time, so handle
these on both resolve and accept:

| Status | Meaning | Suggested UI |
|--------|---------|--------------|
| `404` | Token invalid, unknown, or revoked | "This invite link is no longer valid." |
| `410` | Invite expired (past 7 days) | "This invite has expired — ask for a new one." |
| `409` | Already accepted, or the user is already a member | "This invite was already used." / route them in if logged in. |
| `401` | (accept, existing user) wrong password | Inline "Incorrect password." — let them retry. |
| `422` | Validation (e.g. new user without `name`, password < 8 chars) | Field-level form errors. |

Error bodies follow the app envelope: `{ "detail": "...", "code": "..." }`.

---

## Notes & current limits

- **No email is sent** — sharing the link is manual. (Planned for a later iteration.)
- The invite is **bound to the email** the inviter typed: an existing user must be
  logged into / authenticate the account with that email; a new account is created
  with that email.
- Tokens are **single-use** — once accepted, the link returns `409`.
- Roles an invite can grant: `admin` or `member` only.
