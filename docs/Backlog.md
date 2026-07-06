# Ledgerly — Backlog: Payslip Ingestion & Household Tax Estimation

> Working backlog for a not-yet-started feature, kept separate from [EPICS.md](./EPICS.md)/[PROGRESS.md](./PROGRESS.md) (which reflect the completed A–H epics) until this one is built — at that point its stories should be folded into those two files the same way the "Phase 3 extras" were. Structured the same way: Epic → Feature → Story, `Given/When/Then` acceptance criteria, story points (XS=1, S=2, M=3, L=5, XL=8).
>
> Planned via `/plan` on 2026-07-06 (research: 2 Explore agents on backend/frontend patterns + 1 Plan agent for design; see `SESSION_SUMMARY.md` for the session log and the decisions behind each choice below).

## Context & confirmed decisions

Ledgerly already tracks bank accounts, investments/portfolio, and net worth for the household. This feature adds: upload French salary payslips ("bulletins de paie") month by month, store the data, and estimate French income tax liability — folding in investment income too — reconciled against withholding tax ("prélèvement à la source" / PAS) already deducted at source.

1. Track payslips for **both** Antoine and Camille.
2. **Impatriate regime (régime des impatriés, Art. 155 B CGI) is a generic per-person Settings toggle** — not hardcoded to one household member. Any person can be marked eligible independently, each with their own arrival date, election method, and 8-year window. Antoine is the one who'll actually enable it today (flat-rate 30% election — recruited directly from abroad, not an intra-group transfer), but the data model and UI support enabling it for anyone.
3. Tax depth: **full household estimate** — salary plus investment/capital-gains income, not salary-only PAS tracking.
4. **No transaction linking** — payslip data stays in its own silo; does not create/link Transactions ledger entries (avoids double-counting a bank-imported salary deposit).
5. No sample payslip PDF available yet — parser built generically against standard French bulletin-de-paie fields first, human reviews/corrects everything before saving (same philosophy as the existing AV-valuation-statement import), tuned against a real PDF once one is provided (see "Providing a sample payslip" below).

### Ground-truth findings that shape this backlog (verified against the repo, 2026-07-06)
- `Household`/`Person` (`api/app/domains/accounts/models.py`) are very thin today — nothing about nationality/marital-status/tax-residency/expat-status exists yet. All new, no existing field to repurpose.
- `api/app/infra/tax_rules.py::get_wrapper_hints` is the only existing tax code — pure, DB-free, PEA/AV/PER/PEE milestone hints. The capital-gains work (Feature I4) must call into this, not duplicate its 5yr/8yr math.
- **Investment income gap**: nothing in the app currently computes or persists a *realized* gain at time of sale (only unrealized gain on current positions, average-cost) or a yearly dividend total. Feature I4 must derive both from the raw lot ledger — genuinely new capability, not a reuse of existing computed data.
- `api/app/domains/imports/parsers/pdf_valuation_parser.py` (extract candidates → human reviews/edits → confirm, upsert by natural key) is the direct precedent for the payslip parser/review flow.
- `api/app/domains/pension/` (schemas+router only, stateless, delegates to a pure `core/pension.py` function) is the precedent for the stateless tax-estimate calculator.
- Migrations are linear zero-padded 4-digit ids (`api/alembic/versions/0001`...`0006`); new work continues at `0007`.
- New domain routers must be manually registered in `api/app/main.py::create_app()` — nothing auto-discovers.

### Documented simplifications (surfaced to the user in the UI, not silently applied)
1. Quotient familial "plafonnement" cap — general case only, not single-parent/widowed/disabled variants.
2. Realized capital gains computed at average cost, not FIFO/tax-lot matching (consistent with the rest of the app).
3. PFU-vs-barème "option globale" is a real household-wide annual election in French law; the app computes per-instrument for display but must state that a mixed per-line election isn't how the law actually works.
4. Partial-year YTD extrapolation is linear (ytd/months×12), ignoring bonus/raise timing.
5. Payslip parser accuracy is unverified against a real PDF at ship time.
6. Impatriate regime: eligibility is generic/per-person, but only the flat-30% method is computed; "specific identified premium" is a selectable option that gets flagged/rejected rather than computed, since it wasn't requested.

### Providing a sample payslip without committing it to the codebase
Simplest: just give an absolute file path anywhere on your machine (e.g. Desktop/Downloads) when we start Feature I1 — the agent can read it directly to tune the parser without ever copying it into the repo. If you'd rather keep a reusable fixture across sessions, drop it under `local_samples/` at the repo root (created for this purpose, now in `.gitignore` — git will never see it, even redacted).

---

## EPIC I — Payslip Ingestion & Household Tax Estimation

### Feature I1 — Payslip ingestion (no tax math yet)
**Goal:** payslip history tracked and visualized, independently useful before any tax computation exists.
- **I1-S1** (L) *Payslip PDF parser.* Given a payslip PDF, when uploaded, then a typed candidate is extracted per known field (gross/net imposable/net à payer/taux PAS/PAS withheld/cumuls/période/employer), each editable regardless of whether it was found. `api/app/domains/salary/parsers/pdf_payslip_parser.py`, modeled on `pdf_valuation_parser.py`.
- **I1-S2** (M) *Preview/review/confirm flow.* Given extracted candidates, when I review the screen, then nothing is saved until I confirm — mirrors the AV-valuation review step. `POST /salary/payslips/preview` (no DB write) → `web/src/components/salary/PayslipReviewForm.tsx` → `POST /salary/payslips`.
- **I1-S3** (M) *Upsert by natural key.* Given a re-uploaded/corrected month, when saved, then it upserts on `(person_id, pay_period)` rather than duplicating. Migration `0007_payslips.py`.
- **I1-S4** (S) *Payslip list + delete.* `GET /salary/payslips?person_id=&year=`, `DELETE /salary/payslips/{id}`.
- **I1-S5** (M) *Salary trend chart.* Given saved payslips, when I open `/salary`, then monthly gross/net-taxable/net-paid render as a trend chart. `web/src/components/charts/SalaryTrendChart.tsx`.
- **I1-S6** (S) *i18n.* `nav.salary` + new `salary` namespace, FR+EN.

### Feature I2 — Person / household tax profile settings
**Goal:** capture the facts needed to compute tax — filing status, dependents, and per-person impatriate eligibility — as an explicit, generic Settings surface.
- **I2-S1** (M) *Per-person impatriate toggle.* Given any household member, when I open Settings, then I can independently enable/disable the impatriate regime for them, with their own arrival date and election method (flat-30% / specific-premium — only flat-30% computed). `Person` columns via migration `0008_person_tax_profile.py`.
- **I2-S2** (M) *Household filing status & dependents.* Given the household, when I set filing status (married/pacs vs single) and explicitly pick which existing `Person`s count as dependents, then quotient-familial parts are computable. New `household_tax_settings` table (migration `0009_household_tax_settings.py`) — dependents are an explicit opt-in list, never auto-inferred (so a child isn't silently assumed dependent or not).
- **I2-S3** (S) *Settings UI section.* `web/src/components/settings/TaxProfileSection.tsx`, iterating `usePersons()` with an expandable per-person form, inserted into `settings/page.tsx` between "Household members" and "Labels & rules".
- **I2-S4** (S) *API.* `GET/PUT /tax/profile/{person_id}`, `GET/PUT /tax/household-settings` — new `api/app/api/tax.py`.

### Feature I3 — Salary-only PAS reconciliation
**Goal:** estimate annual income-tax liability from salary alone and compare to PAS already withheld.
- **I3-S1** (L) *Tax-year bracket config.* Given the barème progressif changes yearly via Loi de Finances, when a new year starts, then updating brackets is a data migration, not a code change. New `tax_year_configs` table (migration `0010_tax_year_config.py`), seeded with the 2026 barème.
- **I3-S2** (XL) *Barème + quotient familial engine.* Pure functions in `api/app/core/tax.py`: `apply_bareme`, `compute_parts`, `compute_quotient_tax` (general-case plafonnement only, returns whether the cap bit), golden-tested.
- **I3-S3** (M) *Impatriate exemption, per person.* `apply_impatriate_exemption` (flat 30%) and `impatriate_years_remaining` (8-year window), applied to **every** person with the regime enabled — not a single assumed person.
- **I3-S4** (M) *YTD projection & reconciliation.* `project_annual_from_ytd` (linear extrapolation, documented as a simplification) + `reconcile_withholding` → owe/refund.
- **I3-S5** (L) *Tax estimate endpoint.* `GET /tax/estimate?year=&include_investments=` (stateless, `investment_income: null` until Feature I4), with a per-person breakdown and a `simplifications_applied` list.
- **I3-S6** (L) *`/tax` page.* KPI row (estimated liability, PAS withheld YTD, balance due/refund), `WithholdingReconciliationChart.tsx`, `ImpatriateTimeline.tsx` rendered once per person who has the regime enabled (zero, one, or more — never hardcoded to a name).
- **I3-S7** (S) *i18n.* `nav.tax` + `tax` namespace, disclaimer strings looked up by key (not raw backend text).

### Feature I4 — Investment income folded in (full household estimate)
**Goal:** approximate the real annual "déclaration de revenus" by adding capital gains/dividends to the salary estimate.
- **I4-S1** (XL) *Realized gains from the raw ledger.* `compute_realized_gains_for_year` (average cost per sell-lot — new capability, nothing today computes this) and `sum_dividends_for_year`.
- **I4-S2** (L) *Wrapper exemptions.* `apply_wrapper_exemption` calls `get_wrapper_hints` to zero out/abate gains per PEA-5yr/AV-8yr rules before tax — extends, doesn't duplicate, the existing rules engine.
- **I4-S3** (L) *PFU vs. barème.* `compute_pfu`, `compare_pfu_vs_bareme` — household-wide aggregation, with the "option globale" caveat surfaced explicitly.
- **I4-S4** (M) *Wire into the estimate.* `TaxEstimateOut.investment_income` populated when `include_investments=true`; `/tax` page gains an investment-income breakdown section.

### Feature I5 — Polish
- **I5-S1** (S) *Optional Dashboard tile.* Small "Tax estimate" KPI on `/dashboard` linking to `/tax`.
- **I5-S2** (XS) *Docs housekeeping.* Update `docs/ARCHITECTURE.md` to list the new `salary`/`tax` domains (and `pension`, currently missing too).
- **I5-S3** (S) *Wording pass.* Review all `simplifications_applied` disclaimer copy (FR+EN) for conservative, non-advice-sounding language ("estimation", not "montant dû").
- **I5-S4** *Fold into EPICS.md/PROGRESS.md* once built, same as the "Phase 3 extras" precedent.

---

## Delivery order
I1 → I2 → I3 → I4 → I5, sequentially — each lands as a working, independently testable increment. I1 alone is useful with zero tax math. I2 is prerequisite data entry. I3 is the first real tax number. I4 is the ambitious, most complex piece. I5 is optional polish.

## Verification (per increment)
- Backend: `docker compose -f docker-compose.test.yml run --rm api-test` (always `... down` after) — all tests green, including new golden tests for `core/tax.py`.
- Frontend: `npm run type-check` / `next build` clean (watch for the incidental `tsconfig.json` rewrite).
- Manual: upload a real/synthetic payslip through `/salary` after I1; set up a real tax profile and sanity-check `/tax`'s estimate + disclaimers after I3. This is the household's real tax situation — confirm scope/numbers with the user before treating any estimate as final.
