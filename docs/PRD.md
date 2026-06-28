# Ledgerly — Product Requirements Document (PRD)

> Local-first Personal Finance **Decision** Platform for advanced French households.
> Status: v1 spec · Owner: Product/Architecture · Audience: build team + code agent.

Related: [ARCHITECTURE](./ARCHITECTURE.md) · [DATA_MODEL](./DATA_MODEL.md) · [EPICS](./EPICS.md) · [UX_UI](./UX_UI.md) · [SECURITY](./SECURITY.md) · [DEPLOYMENT](./DEPLOYMENT.md) · [MVP](./MVP.md)

---

## 1. Vision

**Ledgerly helps a financially-literate French household see their entire net worth in one place and make better money decisions — invest vs. prepay, allocate, plan — without sending a single byte to the cloud.**

Most tools stop at *tracking* (Bankin', Linxo, YNAB) or are *cloud aggregators* that scrape bank credentials (a privacy and FinCEN/DSP2 trust problem). Ledgerly is different on three axes:

1. **Local-first & private** — data lives in the user's own Postgres in Docker on their machine. No bank scraping. CSV / manual import only for MVP.
2. **Decision-oriented** — every screen answers a *question* ("Should I prepay or invest?", "Am I on track for FI?"), not just "what happened".
3. **France-native** — first-class support for PEA, Assurance Vie, PER/PERCO/PEE, Livret A, and the tax/wrapper rules that make French wealth tracking genuinely different from US/UK tools.

**One-line positioning:** *Finary's analytics + YNAB's control, running entirely on your own machine.*

### Success metrics (for a self-hosted product)
- **Activation:** user reaches a complete net-worth number within 30 min of first launch (≤ 3 CSV imports + manual balances).
- **Retention proxy:** monthly "reconcile + review" session completed (manual since no scraping).
- **Decision value:** at least one scenario simulation run per user per quarter.
- **Trust:** zero outbound network calls for user financial data (verifiable; see [SECURITY](./SECURITY.md)).

### Explicit non-goals (anti-overengineering)
- ❌ No bank-credential aggregation / Open Banking scraping in v1.
- ❌ No multi-tenant SaaS, no billing, no org/team accounts.
- ❌ No mobile native apps (responsive web is enough).
- ❌ No real-time intraday trading data; **end-of-day prices** only.
- ❌ No automated tax filing. We *inform* tax-aware decisions; we don't file.
- ❌ No crypto exchange API integration in v1 (manual holdings allowed).

---

## 2. Personas

### P1 — "Antoine", the optimizing engineer (primary)
35, software engineer in Lyon, ~€120k TC including ESOP/RSUs. Has a PEA, a Livret A, an Assurance Vie, company PEE + PERCO, and a mortgage. Spreadsheet power-user who has outgrown his spreadsheet. **Wants:** one consolidated net worth, real TWR/XIRR on his PEA, and a defensible answer to "invest the bonus or overpay the mortgage?". **Pain:** manual spreadsheet breaks on multi-currency RSUs and amortization; no risk/allocation view. **Privacy stance:** will not connect bank credentials to a third party.

### P2 — "Camille & Julien", the dual-income family (primary)
Couple, two incomes, Paris suburbs. Individual PEAs each, a **joint** Assurance Vie, a joint bank account + two individual accounts, a mortgage on the primary residence, one car loan. **Wants:** household consolidation with per-person *and* joint views, vacation budget planning, and "are we on track to retire / pay off the house" tracking. **Pain:** ownership splits (who owns what %) and joint vs. individual reporting.

### P3 — "Sophie", the privacy-first FIRE planner (secondary)
42, pursuing financial independence. Tracks a withdrawal-rate / FI number, models different return assumptions, wants asset-allocation drift alerts. Comfortable with Docker. **Wants:** goal tracking + scenario engine. **Pain:** existing FIRE calculators are US-401k-centric and ignore French wrappers.

**Common thread:** tech-savvy, privacy-first, tolerant of *some* manual input in exchange for control and insight.

---

## 3. Use cases (concrete)

| # | As a… | I want to… | So that… |
|---|-------|-----------|----------|
| UC-1 | household member | import my bank CSV and categorize transactions | I see where money goes without manual entry |
| UC-2 | investor | enter PEA buy/sell lots and see TWR + XIRR | I know my *real* return, net of contributions |
| UC-3 | couple | tag accounts as individual/joint with ownership % | reports split correctly per person and household |
| UC-4 | borrower | load my mortgage terms | I see amortization, remaining capital, and interest paid YTD |
| UC-5 | decision-maker | simulate "invest €20k vs. prepay mortgage" under 3 return assumptions | I choose with numbers, not vibes |
| UC-6 | planner | set a "Financial Independence" goal | I track progress and projected date |
| UC-7 | investor | view asset allocation (equity/bonds/cash/RE) and drift vs. target | I rebalance deliberately |
| UC-8 | family | build a vacation budget and track actuals against it | the trip doesn't blow the annual plan |
| UC-9 | user | see net worth as a time series | I understand trajectory and the effect of decisions |
| UC-10 | user | snapshot month-end balances | history is preserved even for manually-tracked assets |

---

## 4. Functional requirements

Notation: **MUST** (MVP), **SHOULD** (fast-follow), **MAY** (later). IDs map to [EPICS](./EPICS.md).

### 4.1 Accounts & household (FR-ACC)
- FR-ACC-1 **MUST** Create persons (self, spouse) and an implicit household.
- FR-ACC-2 **MUST** Create accounts of type *bank | savings | investment-wrapper | liability*, each owned by one person, both persons (joint), with an ownership split (e.g., 50/50, 70/30).
- FR-ACC-3 **MUST** Support multiple banks / institutions per person.
- FR-ACC-4 **MUST** Each account has a base currency (default EUR); foreign assets allowed.
- FR-ACC-5 **SHOULD** Archive (soft-delete) accounts without losing history.

### 4.2 Transactions & expenses (FR-TXN)
- FR-TXN-1 **MUST** Import CSV with a configurable column mapping; persist mappings per institution.
- FR-TXN-2 **MUST** Deduplicate on import (hash of date+amount+description+account).
- FR-TXN-3 **MUST** Categorize transactions; hierarchical categories (Utilities → Electricity).
- FR-TXN-4 **MUST** Auto-categorization via user-defined rules (regex on description → category).
- FR-TXN-5 **MUST** Manual transaction entry + edit + split.
- FR-TXN-6 **SHOULD** Recurring/expected expenses (rent, utilities) flagged and reconciled.
- FR-TXN-7 **MUST** Categories cover the required domains: Utilities (electricity, gas, internet, mobile), Household, Travel.

### 4.3 Investments (FR-INV)
- FR-INV-1 **MUST** Track holdings inside wrappers: **PEA**, **PEA-PME**, **Assurance Vie** (single & joint), **PER/PERO/PERCO**, **PEE**, direct shares/ETFs (CTO), **Livret A** & regulated savings, ESOP/RSU/stock-options.
- FR-INV-2 **MUST** Lot-level transactions (buy/sell/dividend/contribution/fee) with quantity, price, fees, date.
- FR-INV-3 **MUST** Instruments table with ISIN/ticker, asset class, currency, region.
- FR-INV-4 **MUST** Daily/periodic price updates via **manual entry or CSV/price-file import** (no scraping required); pluggable price provider interface for later.
- FR-INV-5 **MUST** Compute per-wrapper and portfolio **TWR** and **XIRR**.
- FR-INV-6 **MUST** Asset allocation breakdown (by class, region, currency, wrapper) + drift vs. target.
- FR-INV-7 **SHOULD** Vesting schedule for ESOP/RSU with vested/unvested split.
- FR-INV-8 **MAY** Tax-wrapper rules engine (PEA 5-year clock, AV 8-year, PER deductibility hint).

### 4.4 Liabilities (FR-LIA)
- FR-LIA-1 **MUST** Model amortizing loans (mortgage, car) with principal, rate, term, start date, payment day.
- FR-LIA-2 **MUST** Generate full amortization schedule (French *amortissement constant*/EMI), remaining capital, interest paid YTD/total.
- FR-LIA-3 **SHOULD** Support extra/partial prepayment and recompute schedule.
- FR-LIA-4 **MAY** Variable-rate and insurance (assurance emprunteur) line items.

### 4.5 Net worth & analytics (FR-AN)
- FR-AN-1 **MUST** Compute net worth = Σ assets − Σ liabilities, per person / joint / household.
- FR-AN-2 **MUST** Net-worth time series from month-end snapshots + price history.
- FR-AN-3 **MUST** Portfolio performance dashboard (TWR, XIRR, contributions vs. growth).
- FR-AN-4 **MUST** Debt vs. investment comparison view (effective mortgage rate vs. expected return).

### 4.6 Scenario simulation (FR-SIM)
- FR-SIM-1 **MUST** "Invest vs. prepay mortgage" simulator with: lump sum and/or monthly amount, horizon, expected return (low/base/high), mortgage rate; outputs net-worth delta over time + breakeven.
- FR-SIM-2 **MUST** Parameterizable return assumptions (deterministic, 3 scenarios minimum).
- FR-SIM-3 **SHOULD** Goal-feasibility simulation (can I hit FI number by year Y?).
- FR-SIM-4 **MAY** Monte Carlo return distribution.
- FR-SIM-5 **MUST** Save/compare named scenarios.

### 4.7 Planning & goals (FR-PLAN)
- FR-PLAN-1 **MUST** Create goals (FI number, house payoff, target portfolio) with target amount + date; track progress %.
- FR-PLAN-2 **MUST** Vacation/travel budget: planned line items, total, and actual-vs-plan tracking once expenses are tagged.
- FR-PLAN-3 **SHOULD** Future expense projections feeding net-worth forecast.

---

## 5. Non-functional requirements

### Performance
- NFR-PERF-1 Dashboard first meaningful paint < **1.5s** on a typical laptop with 5 years of data (~50k transactions, ~5k price rows).
- NFR-PERF-2 CSV import of 10k rows < **5s** including dedup + auto-categorization.
- NFR-PERF-3 Net-worth time series + TWR/XIRR recompute < **2s** (cached materialized snapshots; recompute incrementally).

### Security & privacy (full detail in [SECURITY](./SECURITY.md))
- NFR-SEC-1 **No outbound network calls** carrying user financial data. Optional price fetch is the only egress, off by default, and never sends holdings.
- NFR-SEC-2 Data encrypted **at rest** (Postgres volume / column-level for secrets) and **in transit** (TLS even on localhost for the API).
- NFR-SEC-3 Local authentication (single household, password + argon2id); session via secure httpOnly cookie.
- NFR-SEC-4 GDPR-by-design: full export (JSON/CSV) and hard-delete ("right to erasure") of all data.
- NFR-SEC-5 Secrets (DB creds, encryption keys) via env/secret files, never committed.

### Reliability & data integrity
- NFR-REL-1 All money stored as integer minor units (cents) or `NUMERIC`, never float.
- NFR-REL-2 Imports are idempotent and reversible (import batches can be rolled back).
- NFR-REL-3 Automated, scriptable backup of the Postgres volume; documented restore.

### Usability
- NFR-USE-1 Responsive web (desktop-first, usable on tablet).
- NFR-USE-2 Keyboard-first navigation (command palette), Linear/Notion-grade speed (see [UX_UI](./UX_UI.md)).
- NFR-USE-3 i18n-ready (EN + FR), EUR formatting (`1 234,56 €`), French date format.

### Maintainability / portability
- NFR-MNT-1 `docker compose up` brings the whole stack up on one node.
- NFR-MNT-2 Modular monolith backend; domains decoupled enough to extract later.
- NFR-MNT-3 Typed end-to-end (Python type hints + Pydantic; TS on frontend); OpenAPI contract generated.

---

## 6. Assumptions & constraints
- Single household per deployment (multi-user is one couple, not a SaaS).
- User accepts manual/CSV input as the price of privacy.
- End-of-day pricing is sufficient for decisions.
- French wrappers and a EUR base currency are first-class; other currencies are converted for display.
- Runs on a modern laptop/NAS with Docker; no GPU, no cluster.

---

## 7. Risks & mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Manual price entry is tedious | Adoption drops | CSV price import + optional pluggable provider (off by default) |
| TWR/XIRR correctness disputed | Trust loss | Golden-test the math against known datasets; show methodology |
| Ownership-split reporting confuses | Wrong numbers | Explicit per-person vs. household toggle, documented model |
| Scope creep (tax engine, scraping) | Slips MVP | Hard non-goals above; tax/rules engine is MAY/Phase 3 |
| Encryption key loss | Data unrecoverable | Documented key backup; recovery codes; warn on first run |
