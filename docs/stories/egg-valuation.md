# Story — Egg value & profit from egg sales

> Origin: farm-owner feedback — *"Registrar profit por venta de huevos
> (producción), cómo se refleja el valor del huevo?"*
> Model decided via web research — see [Decisions](#decisions-locked).

> **Status (shipped, 2026).** Farm-level egg value shipped as
> `GET /farms/{farm_id}/reports/sales-value` (below, still accurate). The
> **per-coop** goal also shipped — but via a *different* mechanism than the
> "tag each sale to a coop" design proposed further down: `GET
> /farms/{farm_id}/reports/produce-outcome` attributes pooled produce revenue
> back to each producer by **derived FIFO** over daily contribution baskets
> (#47). No `producer_asset_id` column was added, no per-sale coop tag, and no
> `/reports/egg-value` endpoint — those sections below are **superseded**, kept
> only for the rationale. Also note: after #48 eggs are a **produce** asset
> (kind=`produce`), not a material.

## User story

As a farm owner, I want each egg sale to record **how much an egg is worth** and
**what I made per coop**, so the app can show egg value and margin — not just a
lump sum of income.

## What already exists

- A sale (`POST /farms/{farm_id}/assets/{asset_id}/sales`) writes one `INCOME`
  event with a **total `amount`** and decrements egg inventory — atomically
  (`material_sale/actions.py`). The income lands on the **eggs produce asset**.
- `PRODUCTION`/harvest events carry **quantity only, no money**
  (`event/schemas.py`).
- `cost-per-unit` already computes a per-coop **cost** (feed + direct expense ÷
  production qty) on the coop.

## What's missing (the gap)

There is **no per‑unit value** anywhere (only `cost_per_unit`, which is a cost).
The egg's worth is implicit as `amount ÷ quantity` at sale time. And egg income
sits on the **shared eggs produce asset**, not the coop — so per‑coop profit
can't be attributed today. *(Since shipped: `produce-outcome` closes this gap by
FIFO-attributing pooled produce revenue to each producer.)*

## Shipped in v1 — `GET /reports/sales-value`

Delivered now: a **realized sale value per unit, per asset** report — no schema
change, no domain assumptions, derived entirely from existing `material_sale`
events. Per asset sold in the window: `income_total`, `quantity_sold`,
`value_per_unit = income ÷ quantity` (the weighted-average price actually
received, e.g. value per egg). Counts only `material_sale` income + its paired
decrement (manual income excluded); mixed sale units → `ambiguous=true` with a
null `value_per_unit`; assets with no sales don't appear. Paired with the
existing `cost-per-unit` report (the cost floor), this answers *"cómo se refleja
el valor del huevo"* and "what did I make" at the farm/asset level.

## Superseded — per-coop shipped via FIFO, not sale-tagging

> **This section is historical.** The per-coop goal shipped as
> `GET /farms/{farm_id}/reports/produce-outcome`: pooled produce is fungible, so
> per-producer income is **never stored or tagged on the sale** — each outflow's
> revenue is split back to producers by **derived FIFO** over daily contribution
> baskets (`produce_lot`). Correcting a harvest re-derives attribution on the
> next request; nothing is re-booked. Currencies are never summed
> (`has_other_currency`); stock with no lot behind it surfaces as
> `unattributed_quantity` / `unattributed_income`. No `producer_asset_id` column
> and no `egg-value` endpoint were added. The sale-tagging design below was the
> original proposal, kept for rationale only.

The per-coop / tagging design below came from research-backed *defaults*, not a
real user (see [questions for the farmer](#questions-for-the-farmer) — largely
resolved by the FIFO-derivation approach, which needs no per-sale coop tag).

1. **Tag each egg sale to a coop (the producing asset).** Add an *optional*
   producing‑coop reference to the egg sale; the booked `INCOME` is then
   attributed directly to that coop. This is the industry norm (PoultryCare,
   SmartBird, DataDaur all tag sales to a flock) and it **removes the attribution
   ambiguity entirely** — far cleaner than splitting pooled revenue. When a sale
   is left untagged it counts at the farm / eggs‑asset level only.
   ([PoultryCare](https://www.poultry.care/features/batch-wise-pl-analysis),
   [Iowa State enterprise accounting](https://www.extension.iastate.edu/agdm/wholefarm/html/c6-34.html))
2. **Derive the unit price, don't store it.** `value_per_egg = Σ(sale income) ÷
   Σ(eggs sold)`, weighted‑average over the period. This is the standard ag‑econ
   "price received" recovery and the IAS 2‑sanctioned weighted‑average for
   fungible goods (eggs are the textbook case). The user confirmed egg prices are
   roughly uniform within a period, so the weighted‑average is accurate. No
   per‑sale `unit_price` field in v1.
   ([Penn State](https://extension.psu.edu/budgeting-for-agricultural-decision-making),
   [CFI weighted-average](https://corporatefinanceinstitute.com/resources/accounting/weighted-average-cost-method/))
3. **Normalize egg quantity to single eggs internally** (×12 for per‑dozen
   display). Never average a per‑dozen figure against a per‑egg figure — keep
   `amount` and `quantity` both in eggs before dividing.
4. **Call it "margin over variable cost", not "profit".** `cost_per_unit` is
   variable cost only (feed + direct expense, no overhead), so `value_per_egg −
   cost_per_egg` is a **gross margin**, not net profit.
   ([NSW DPIRD](https://www.dpird.nsw.gov.au/agriculture/budgets/about))

## Metrics

- **value_per_egg** = `Σ(material_sale INCOME amount, period) ÷ Σ(eggs sold, period)`
- **cost_per_egg** = existing `cost_per_unit` on the coop
- **margin_per_egg** = `value_per_egg − cost_per_egg`
- **margin_per_coop** = `margin_per_egg × coop_eggs_sold` (income tagged to the coop)

## Acceptance criteria

- An egg sale accepts an optional producing‑coop reference; the report attributes
  that sale's income to the coop. Untagged sales appear in the farm/eggs‑asset
  total only.
- `GET /farms/{farm_id}/reports/egg-value?date_from=&date_to=` returns, per eggs
  asset: `eggs_sold`, `income_total`, `value_per_egg`; and per tagged coop:
  `cost_per_egg`, `margin_per_egg`, `margin_per_coop`.
- Selling 24 eggs for 240 reports `value_per_egg = 10.00`.
- **No sales in period** → `value_per_egg: null` ("no sales"), never `0`.
- **Sold but no cost** (`cost_per_unit` null) → `margin: null` ("cost unknown"),
  never margin = full revenue.
- **$0 giveaways** are excluded from the price denominator.
- Currencies are never mixed (same rule as the profitability report).

## Out of scope (v1)

Inventory/COGS valuation of **unsold** egg stock; FIFO / cost layers (converge
with weighted‑average for fast‑turning eggs); explicit per‑sale unit‑price entry
(deferred hedge — `amount/quantity` can be exposed as a computed read field
later); fixed/overhead allocation to reach true **net** profit; production‑share
allocation of pooled revenue (obviated by sale‑tagging).

## Implementation note (for the deferred per-coop work)

Tagging needs a queryable link from the egg‑sale `INCOME` event back to the coop.
Decide at build time: a nullable `producer_asset_id` on the sale persisted on the
event vs. a `payload` entry — a real column is more SARGable for the per‑coop
`GROUP BY`, but touches the core `Event` model, so weigh against the established
`payload.source` tagging convention.

## Questions for the farmer

Answers turn the deferred per-coop design from guesses into real decisions:

1. Do you want egg value/profit broken down **per coop**, or is a farm-level
   "what's an egg worth / what did I make" enough?
2. When you sell eggs, do you know **which coop** they came from (would you tag
   the sale), or do eggs from several coops get mixed before selling?
3. Do you ever sell eggs at **different prices in the same period** (retail vs
   bulk, friends-and-family)? Roughly what spread?
4. Do you sell by the **dozen, loose egg, or both**?
5. Do you **give eggs away / eat them at home**, and do you want that recorded?
