# Ledgerly — Build Progress

Tracks every story from [EPICS.md](./EPICS.md) across all three phases.
Status: `[ ]` TODO · `[~]` IN PROGRESS · `[x]` DONE

Updated by the build agent after each story is completed.

---

## EPIC A — Household & Accounts

### Feature A1 — Persons & household
- [x] **A1-S1** (P1) Create persons — self + spouse → household
- [x] **A1-S2** (P1) Single-household auth — password + argon2id

### Feature A2 — Accounts & ownership
- [x] **A2-S1** (P1) Create account (type + institution + currency)
- [x] **A2-S2** (P1) Ownership split (joint 50/50 etc.)
- [x] **A2-S3** (P2) Archive account

---

## EPIC B — Transactions & Expenses

### Feature B1 — CSV import
- [x] **B1-S1** (P1) Mapped CSV import + saved column mapping
- [x] **B1-S2** (P1) Dedup on re-import (sha256 hash)
- [x] **B1-S3** (P2) Rollback import batch

### Feature B2 — Categorization
- [x] **B2-S1** (P1) Hierarchical categories (Utilities → Electricity)
- [x] **B2-S2** (P1) Rule-based auto-categorize (regex → category)
- [x] **B2-S3** (P1) Manual entry & split
- [x] **B2-S4** (P2) Recurring/expected expenses — flag missing

---

## EPIC C — Investments & Portfolio

### Feature C1 — Wrappers & holdings
- [x] **C1-S1** (P1) Create wrapper accounts (PEA/AV/PER/PEE/Livret A/CTO)
- [x] **C1-S2** (P1) Lot transactions (buy/sell/dividend/contribution/fee)
- [x] **C1-S3** (P1) Instruments (ISIN/ticker, class, region, currency)

### Feature C2 — Prices
- [x] **C2-S1** (P1) Manual/CSV price import (ISIN+date+close)
- [x] **C2-S2** (P3) Pluggable price provider (off by default)

### Feature C3 — Performance & allocation
- [x] **C3-S1** (P1) TWR + XIRR per wrapper + total
- [x] **C3-S2** (P1) Asset allocation + drift vs. target
- [x] **C3-S3** (P2) ESOP/RSU vesting schedule (vested/unvested)

---

## EPIC D — Liabilities

### Feature D1 — Loans & amortization
- [x] **D1-S1** (P1) Model loan + full amortization schedule
- [x] **D1-S2** (P1) Debt view — remaining capital + interest YTD/total
- [x] **D1-S3** (P2) Prepayment recompute (term or payment reduction)

---

## EPIC E — Net Worth & Analytics

### Feature E1 — Net worth
- [x] **E1-S1** (P1) Net worth now (person/joint/household)
- [x] **E1-S2** (P1) Net worth over time (time series)
- [x] **E1-S3** (P1) Snapshot job (month-end freeze)

---

## EPIC F — Scenario Simulation

### Feature F1 — Invest vs. prepay
- [x] **F1-S1** (P1) Invest-vs-prepay simulator (low/base/high, breakeven)
- [x] **F1-S2** (P1) Save & compare named scenarios
- [x] **F1-S3** (P3) Monte Carlo (percentile bands)

### Feature F2 — Goal feasibility
- [x] **F2-S1** (P2) Goal feasibility (projected date + on/off-track)

---

## EPIC G — Planning & Goals

### Feature G1 — Goals
- [x] **G1-S1** (P1) Create & track goal (FI number, progress %)

### Feature G2 — Travel/vacation budget
- [x] **G2-S1** (P2) Vacation budget (plan-vs-actual)
- [x] **G2-S2** (P3) Future expense projection in net-worth forecast

---

## EPIC H — Platform, Security & Ops

### Feature H1 — Security & privacy
- [x] **H1-S1** (P1) Encryption at rest + TLS
- [x] **H1-S2** (P1) Argon2id auth + session cookie
- [x] **H1-S3** (P2) GDPR export (JSON/CSV) + hard erase
- [x] **H1-S4** (P1) Secrets via env/Docker secret files

### Feature H2 — Deploy & data
- [x] **H2-S1** (P1) `docker compose up` one-node stack
- [x] **H2-S2** (P1) Backup/restore scripts
- [x] **H2-S3** (P1) OpenAPI contract + typed TS client

### Feature H3 — UX shell
- [x] **H3-S1** (P1) App shell + command palette (⌘K)
- [x] **H3-S2** (P1) EN/FR i18n + EUR formatting

---

## Phase 3 extras (C2-S2, F1-S3, G2-S2 + infra)
- [x] **P3-1** Pluggable price provider (`HttpPriceProvider`, daily scheduler job at 18:30 UTC)
- [x] **P3-2** Tax-wrapper rules engine (`get_wrapper_hints`: PEA 5yr, AV 8yr, PER, PEE/PERCO blocks)
- [x] **P3-3** `GET /accounts/{id}/tax-hints` endpoint
- [x] **P3-4** Monte Carlo API (`POST /scenarios/monte-carlo`, 1000 paths, p10/p50/p90)
- [x] **P3-5** Monte Carlo frontend page (`/scenarios/monte-carlo`)
- [x] **P3-6** Migration 0002 — `accounts.opened_at`, `accounts.created_at`

---

## EPIC I — Payslip Ingestion & Household Tax Estimation *(post-MVP, see [EPICS](./EPICS.md))*

### Feature I1 — Payslip ingestion
- [x] **I1-S1** Payslip PDF parser (`pdf_payslip_parser.py`)
- [x] **I1-S2** Preview/review/confirm flow
- [x] **I1-S3** Upsert by natural key `(person_id, pay_period)`
- [x] **I1-S4** Payslip list + delete
- [x] **I1-S5** Salary trend chart
- [x] **I1-S6** i18n (FR+EN)

### Feature I2 — Person / household tax profile settings
- [x] **I2-S1** Per-person impatriate toggle (arrival date + election method)
- [x] **I2-S2** Household filing status & explicit dependents list
- [x] **I2-S3** Settings UI section (`TaxProfileSection.tsx`)
- [x] **I2-S4** API (`/tax/profile/{id}`, `/tax/household-settings`)

### Feature I3 — Salary-only PAS reconciliation
- [x] **I3-S1** Tax-year bracket config (`tax_year_configs` table)
- [x] **I3-S2** Barème + quotient familial engine (`core/tax.py`, golden-tested)
- [x] **I3-S3** Impatriate flat-30% exemption per person
- [x] **I3-S4** YTD projection & withholding reconciliation
- [x] **I3-S5** Tax estimate endpoint (`GET /tax/estimate`)
- [x] **I3-S6** `/tax` page (KPIs, reconciliation chart, impatriate timeline)
- [x] **I3-S7** i18n — disclaimers looked up by key

### Feature I4 — Investment income folded in
- [x] **I4-S1** Realized gains (average cost) + dividend summing
- [x] **I4-S2** Wrapper exemptions (PEA 5yr / AV 8yr) via `get_wrapper_hints`
- [x] **I4-S3** PFU vs. barème comparison
- [x] **I4-S4** Wired into `GET /tax/estimate?include_investments=true`

### Feature I5 — Polish
- [x] **I5-S1** Dashboard "Tax estimate" KPI tile linking to `/tax`
- [x] **I5-S2** ARCHITECTURE.md housekeeping (`salary`/`tax`/`pension` domains)
- [x] **I5-S3** Disclaimer wording pass (reviewed, already conservative)
- [x] **I5-S4** Folded into EPICS.md/PROGRESS.md (this entry)

---

## EPIC J — French Expat Tax Filing Module *(post-MVP, see [EPICS](./EPICS.md))*

### Feature J1 — Residency & per-person tax-filing facts
- [x] **J1-S1/S2** Per-person residency profile (`PersonTaxResidency`) + API
- [x] **J1-S3** Wizard residency step (`ResidencyStep.tsx`)
- [x] **J1-S4** Treaty metadata reference (seeded India/US/UK/Canada/Germany)

### Feature J2 — Foreign income/account data entry + parsers
- [x] **J2-S1/S2** RSU vesting + ESPP purchase parsers (`VestingSchedule` + `InvestmentLot` ESPP fields)
- [x] **J2-S3/S4** Foreign dividend + foreign bank statement parsers
- [x] **J2-S5** Confirm flows persist the original document (Feature J3)
- [x] **J2-S6** `Account.country_code` + Accounts page field
- [x] **J2-S7** Manual CRUD for both declaration types
- [x] **J2-S8** i18n

### Feature J3 — Encrypted document storage
- [x] **J3-S1/S2** Crypto helper (`document_crypto.py`) + `TaxDocument` table
- [x] **J3-S3/S4** List/download/delete endpoints
- [x] **J3-S5** GDPR export/erase wiring (Epic I + Epic J tables)

### Feature J4 — `tax_filing_rules` engine
- [x] **J4-S1/S2** Foreign tax credit — credit method + exemption avec taux effectif
- [x] **J4-S3** Per-line elimination-method resolution
- [x] **J4-S4/S5** Box mapping (2042/2047/3916)
- [x] **J4-S6** Validation (`validate_filing_inputs`)

### Feature J5 — `FilingSnapshot` compute/validate/lock
- [x] **J5-S1** Compute endpoint (upsert, 409 if locked)
- [x] **J5-S2/S3** Stable read + validate endpoints
- [x] **J5-S4** Lock/unlock endpoints

### Feature J6 — Cerfa-style PDF generation
- [x] **J6-S1** Box-layout data + generic `reportlab` renderer
- [x] **J6-S2** Generate-pdf endpoint (single form or zip bundle)
- [x] **J6-S3** Facsimile disclaimer footer

### Feature J7 — Frontend wizard
- [x] **J7-S1** `StepIndicator` component
- [x] **J7-S2-S6** 5-step wizard (Residency/ForeignIncome/ForeignAccounts/Deductions&Credits/Summary&Validation)
- [x] **J7-S7/S8** Page assembly + i18n (96 FR/EN keys)

### Feature J8 — Polish
- [x] **J8-S1** Dashboard "Tax filing" KPI tile linking to `/tax-filing`
- [x] **J8-S2** ARCHITECTURE.md housekeeping (`tax_filing` domain + `pdf`/`parsers` sub-packages)
- [x] **J8-S3** Disclaimer wording pass (reviewed, already conservative)
- [x] **J8-S4** Folded into EPICS.md/PROGRESS.md (this entry)

---

## Phase summary
| Phase | Stories | Done | Pct |
|-------|---------|------|-----|
| P1 (MVP) | 25 | 25 | 100% |
| P2 | 8 | 8 | 100% |
| P3 | 4 | 4 | 100% |
| **Total** | **37** | **37** | **100%** |

---

## Build log
| Date | Action |
|------|--------|
| 2026-06-28 | PROGRESS.md created, build started |
| 2026-06-28 | P1 complete: all 25 MVP stories implemented |
| 2026-06-28 | P2 complete: rollback, archive, vesting, prepayment, GDPR |
| 2026-06-28 | P3 complete: price provider, tax rules, Monte Carlo, migration 0002 |
| 2026-07-06 | Epic I planned (payslip ingestion + household tax estimation), `docs/Backlog.md` written |
| 2026-07-06 | I1 complete: payslip ingestion (parser, review flow, upsert, trend chart) |
| 2026-07-06 | I2 complete: person/household tax profile settings (impatriate toggle, filing status, dependents) |
| 2026-07-06 | I3 complete: salary-only PAS reconciliation (barème/quotient-familial engine, `/tax` page) |
| 2026-07-07 | I4 complete: investment income folded in (realized gains, wrapper exemptions, PFU vs. barème) |
| 2026-07-07 | I5 complete: polish (Dashboard tile, docs housekeeping, wording review) — Epic I fully done, folded into EPICS.md/PROGRESS.md |
| 2026-07-07 | Epic J planned (French expat tax filing module), `docs/Backlog.md` written |
| 2026-07-07 | J1 complete: residency profile + treaty metadata reference |
| 2026-07-07 | J3-S1/S2 complete: encrypted document storage schema + crypto helper (pulled ahead of J2) |
| 2026-07-07 | J2 complete: RSU vesting/ESPP/foreign-income/foreign-account parsers + manual CRUD + `Account.country_code` |
| 2026-07-07 | J3-S3-S5 complete: document list/download/delete + GDPR export/erase wiring |
| 2026-07-07 | J4 complete: `tax_filing_rules` engine (foreign tax credit, box mapping, validation) |
| 2026-07-07 | J5 complete: `FilingSnapshot` compute/validate/lock endpoints |
| 2026-07-07 | J6 complete: Cerfa-style PDF facsimile generation (2042/2047/3916) |
| 2026-07-07 | J7 complete: frontend 5-step wizard, verified live in-browser against the real household |
| 2026-07-07 | J8 complete: polish (Dashboard tile, docs housekeeping, wording review) — Epic J fully done, folded into EPICS.md/PROGRESS.md |
