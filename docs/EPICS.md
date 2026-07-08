# Ledgerly — Epics, Features & User Stories

Backlog structured as **Epic → Feature → Story**. Each story has an ID, a `Given/When/Then` acceptance criterion, and a phase tag (P1/P2/P3 — see [MVP](./MVP.md)). Requirement IDs reference [PRD](./PRD.md).

Story point scale: XS=1, S=2, M=3, L=5, XL=8.

---

## EPIC A — Household & Accounts  *(foundation)*
**Goal:** model people, ownership, and accounts so every downstream number can be split per-person/joint.

### Feature A1 — Persons & household
- **A1-S1** (P1, S) *Create persons.* Given onboarding, when I add "self" and "spouse", then both exist and a household is implied. (FR-ACC-1)
- **A1-S2** (P1, S) *Single-household auth.* Given first launch, when I set a password, then login is required thereafter. (NFR-SEC-3)

### Feature A2 — Accounts & ownership
- **A2-S1** (P1, M) *Create account.* Given a person, when I add an account with type + institution + currency, then it appears in the account list. (FR-ACC-2/3/4)
- **A2-S2** (P1, M) *Ownership split.* Given a joint account, when I set 50/50, then reports allocate balances accordingly. (FR-ACC-2, UC-3)
- **A2-S3** (P2, S) *Archive account.* Given an old account, when I archive it, then it leaves active views but history is retained. (FR-ACC-5)

---

## EPIC B — Transactions & Expenses
**Goal:** get money-in/out into the system cheaply and categorized.

### Feature B1 — CSV import
- **B1-S1** (P1, L) *Mapped CSV import.* Given a bank CSV, when I map columns (date/amount/desc), then rows import and the mapping is saved for that institution. (FR-TXN-1)
- **B1-S2** (P1, M) *Dedup.* Given a re-imported file, when rows match an existing hash, then they are skipped and reported. (FR-TXN-2)
- **B1-S3** (P2, M) *Rollback batch.* Given an import batch, when I undo it, then all its rows are removed. (NFR-REL-2)

### Feature B2 — Categorization
- **B2-S1** (P1, M) *Hierarchical categories.* Given the category tree, when I assign "Utilities → Electricity", then the txn rolls up under Utilities. (FR-TXN-3/7)
- **B2-S2** (P1, M) *Rule-based auto-categorize.* Given a rule `/EDF/ → Electricity`, when matching txns import, then they auto-categorize. (FR-TXN-4)
- **B2-S3** (P1, S) *Manual entry & split.* Given a cash expense, when I add/split it, then it appears with categories. (FR-TXN-5)
- **B2-S4** (P2, M) *Recurring/expected.* Given monthly rent, when the month passes, then a missing expected expense is flagged. (FR-TXN-6)

---

## EPIC C — Investments & Portfolio
**Goal:** accurate holdings, prices, and *real* returns inside French wrappers.

### Feature C1 — Wrappers & holdings
- **C1-S1** (P1, L) *Create wrapper accounts.* Given investment types, when I add a PEA/AV/PER/PEE/Livret A, then each is modeled with its rules-metadata. (FR-INV-1)
- **C1-S2** (P1, L) *Lot transactions.* Given a wrapper, when I record buy/sell/dividend/contribution/fee lots, then holdings recompute. (FR-INV-2)
- **C1-S3** (P1, M) *Instruments.* Given an ISIN, when I add an instrument with class/region/currency, then lots reference it. (FR-INV-3)

### Feature C2 — Prices
- **C2-S1** (P1, M) *Manual/CSV price import.* Given a price file, when I import EOD prices by ISIN+date, then valuations update. (FR-INV-4)
- **C2-S2** (P3, M) *Pluggable price provider.* Given an optional provider, when enabled, then prices fetch on demand (off by default, no holdings sent). (FR-INV-4, NFR-SEC-1)

### Feature C3 — Performance & allocation
- **C3-S1** (P1, XL) *TWR + XIRR.* Given holdings + cashflows, when I open performance, then per-wrapper and total TWR & XIRR display. (FR-INV-5)
- **C3-S2** (P1, L) *Asset allocation + drift.* Given a target allocation, when I view allocation, then actual vs. target drift shows by class/region/currency. (FR-INV-6)
- **C3-S3** (P2, M) *ESOP/RSU vesting.* Given a vesting schedule, when I view equity comp, then vested/unvested split shows. (FR-INV-7)

---

## EPIC D — Liabilities
**Goal:** know exactly what is owed and what interest costs.

### Feature D1 — Loans & amortization
- **D1-S1** (P1, L) *Model loan.* Given mortgage/car terms, when saved, then a full amortization schedule generates. (FR-LIA-1/2)
- **D1-S2** (P1, M) *Debt view.* Given loans, when I open Debt, then remaining capital + interest paid YTD/total show. (FR-LIA-2, FR-AN-4)
- **D1-S3** (P2, M) *Prepayment.* Given a partial prepayment, when applied, then the schedule recomputes (term or payment reduction). (FR-LIA-3)

---

## EPIC E — Net Worth & Analytics
**Goal:** one trusted number, over time, sliceable.

### Feature E1 — Net worth
- **E1-S1** (P1, L) *Net worth now.* Given all accounts, when I open Dashboard, then net worth (person/joint/household) shows. (FR-AN-1)
- **E1-S2** (P1, L) *Net worth over time.* Given month-end snapshots, when I view history, then a time series renders. (FR-AN-2, UC-9/10)
- **E1-S3** (P1, S) *Snapshot job.* Given month end, when the snapshot runs, then balances are frozen for history. (FR-AN-2)

---

## EPIC F — Scenario Simulation  *(the differentiator)*
**Goal:** turn decisions into numbers.

### Feature F1 — Invest vs. prepay
- **F1-S1** (P1, XL) *Invest vs. prepay simulator.* Given a lump sum/monthly amount, horizon, mortgage rate, and low/base/high returns, when I run it, then net-worth-delta-over-time + breakeven render. (FR-SIM-1/2)
- **F1-S2** (P1, M) *Save & compare scenarios.* Given a run, when I save it, then I can compare named scenarios side by side. (FR-SIM-5)
- **F1-S3** (P3, L) *Monte Carlo.* Given a return distribution, when I run MC, then percentile bands show. (FR-SIM-4)

### Feature F2 — Goal feasibility
- **F2-S1** (P2, L) *Goal feasibility.* Given an FI number + date, when I run feasibility, then projected date + on/off-track shows. (FR-SIM-3, FR-PLAN-1)

---

## EPIC G — Planning & Goals
### Feature G1 — Goals
- **G1-S1** (P1, M) *Create & track goal.* Given a goal target + date, when assets change, then progress % updates. (FR-PLAN-1, UC-6)
### Feature G2 — Travel/vacation budget
- **G2-S1** (P2, M) *Vacation budget.* Given planned line items, when I tag actual expenses to the trip, then plan-vs-actual shows. (FR-PLAN-2, UC-8)
- **G2-S2** (P3, M) *Future expense projection.* Given planned future expenses, when forecasting, then they feed the net-worth projection. (FR-PLAN-3)

---

## EPIC H — Platform, Security & Ops *(cross-cutting)*
### Feature H1 — Security & privacy
- **H1-S1** (P1, M) *Encryption at rest + TLS.* (NFR-SEC-2) · **H1-S2** (P1, S) *Argon2id auth + session.* (NFR-SEC-3)
- **H1-S3** (P2, M) *GDPR export + erase.* (NFR-SEC-4) · **H1-S4** (P1, S) *Secrets via env/secret files.* (NFR-SEC-5)
### Feature H2 — Deploy & data
- **H2-S1** (P1, M) *`docker compose up` one-node stack.* (NFR-MNT-1) · **H2-S2** (P1, S) *Backup/restore scripts.* (NFR-REL-3)
- **H2-S3** (P1, S) *OpenAPI contract + typed client.* (NFR-MNT-3)
### Feature H3 — UX shell
- **H3-S1** (P1, M) *App shell + command palette nav.* (NFR-USE-2) · **H3-S2** (P1, S) *EN/FR i18n + EUR formatting.* (NFR-USE-3)

---

## EPIC I — Payslip Ingestion & Household Tax Estimation *(post-MVP, built 2026-07-06/07)*
**Goal:** track monthly French salary payslips and estimate household income-tax liability (salary + investment income), reconciled against withholding (PAS) already deducted. Folded in from `docs/Backlog.md`, which has the full acceptance criteria and documented simplifications — see there for detail.

### Feature I1 — Payslip ingestion
- **I1-S1** (L) *Payslip PDF parser.* Given a payslip PDF, when uploaded, then gross/net-imposable/net-à-payer/taux-PAS/PAS-withheld/cumuls/période/employer are extracted as an editable candidate.
- **I1-S2** (M) *Preview/review/confirm flow.* Nothing is saved until reviewed and confirmed.
- **I1-S3** (M) *Upsert by natural key.* A re-uploaded/corrected month replaces rather than duplicates, keyed on `(person_id, pay_period)`.
- **I1-S4** (S) *Payslip list + delete.*
- **I1-S5** (M) *Salary trend chart.*
- **I1-S6** (S) *i18n (FR+EN).*

### Feature I2 — Person / household tax profile settings
- **I2-S1** (M) *Per-person impatriate toggle* (régime des impatriés, Art. 155 B CGI) — generic, any person independently enabled with their own arrival date + election method.
- **I2-S2** (M) *Household filing status & dependents* — explicit opt-in dependents list, never auto-inferred.
- **I2-S3** (S) *Settings UI section.*
- **I2-S4** (S) *API* (`GET/PUT /tax/profile/{person_id}`, `GET/PUT /tax/household-settings`).

### Feature I3 — Salary-only PAS reconciliation
- **I3-S1** (L) *Tax-year bracket config* — barème lives in a `tax_year_configs` table, not code.
- **I3-S2** (XL) *Barème + quotient familial engine* (`core/tax.py`, golden-tested).
- **I3-S3** (M) *Impatriate exemption* (flat-30% only, per person).
- **I3-S4** (M) *YTD projection & reconciliation* (linear extrapolation).
- **I3-S5** (L) *Tax estimate endpoint* (`GET /tax/estimate`).
- **I3-S6** (L) *`/tax` page* — KPI row, withholding-reconciliation chart, impatriate timeline.
- **I3-S7** (S) *i18n* — disclaimer strings looked up by key.

### Feature I4 — Investment income folded in
- **I4-S1** (XL) *Realized gains from the raw ledger* (`compute_realized_gains_for_year`, average cost) + dividend summing.
- **I4-S2** (L) *Wrapper exemptions* — PEA 5yr / AV 8yr, via the existing `get_wrapper_hints` rules engine.
- **I4-S3** (L) *PFU vs. barème* comparison, household-wide.
- **I4-S4** (M) *Wire into the estimate* — `investment_income` populated when `include_investments=true`.

### Feature I5 — Polish
- **I5-S1** (S) *Optional Dashboard tile* — small "Tax estimate" KPI linking to `/tax`.
- **I5-S2** (XS) *Docs housekeeping* — `salary`/`tax`/`pension` domains listed in ARCHITECTURE.md.
- **I5-S3** (S) *Wording pass* — reviewed all `simplifications_applied` disclaimer copy (FR+EN); already conservative/estimate-framed, no changes needed.
- **I5-S4** *Folded into EPICS.md/PROGRESS.md* (this section).

---

## EPIC J — French Expat Tax Filing Module *(post-MVP, built 2026-07-07)*
**Goal:** a filing-preparation layer on top of Epic I's tax *estimate* — foreign-source income (Form 2047), foreign bank accounts (Form 3916), RSU/ESPP equity comp, encrypted source-document retention, and a Cerfa-style PDF facsimile — for a foreigner who is a French tax resident (builds on the impatriate-regime work). Folded in from `docs/Backlog.md`, which has the full acceptance criteria and documented simplifications — see there for detail.

### Feature J1 — Residency & per-person tax-filing facts
- **J1-S1/S2** (M/S) *Per-person residency profile* (`PersonTaxResidency` — home country, home-country tax ID, French tax number) + API.
- **J1-S3** (S) *Wizard residency step* (`ResidencyStep.tsx`, reused as Feature J7's first wizard step).
- **J1-S4** (M) *Treaty metadata reference* — seeded for India/US/UK/Canada/Germany; any other country flags `treaty_method_defaulted_unseeded_country`.

### Feature J2 — Foreign income/account data entry + parsers
- **J2-S1/S2** (L/L) *RSU vesting + ESPP purchase parsers* — wire the long-dormant `VestingSchedule` table and two new nullable `InvestmentLot` columns (`fmv_at_acquisition`, `discount_pct`) into real use for the first time.
- **J2-S3/S4** (M/M) *Foreign dividend + foreign bank statement parsers* → `ForeignIncomeDeclaration`/`ForeignAccountDeclaration` candidates.
- **J2-S5** (M) *Confirm flows also persist the original document* via Feature J3's encrypted storage.
- **J2-S6** (S) *`Account.country_code`* (null = France, same convention as `opened_at`) + Accounts page field.
- **J2-S7** (M) *Manual CRUD* for both declaration types (entries with no source document).
- **J2-S8** (S) *i18n.*

### Feature J3 — Encrypted document storage
- **J3-S1/S2** (L/M) *Crypto helper + `TaxDocument` table* — Fernet encryption keyed from the previously-unused `Settings.encryption_key`; built ahead of Feature J2 since its confirm flows depend on it.
- **J3-S3/S4** (S/S) *List/download/delete* endpoints (download decrypts + streams, logs the access).
- **J3-S5** (M) *GDPR wiring* — `export_all_data()`/`erase_all_data()` extended for every Epic J table, and the pre-existing gap that Epic I's own tables were never in the erase list either was closed at the same time. Seeded reference tables (`tax_year_configs`, `treaty_metadata`) are deliberately excluded from both — not personal data.

### Feature J4 — `tax_filing_rules` engine
- **J4-S1/S2** (L/L) *Foreign tax credit* — both real elimination methods (crédit d'impôt égal à l'impôt français; exemption avec taux effectif), golden-tested against `core/tax.py`'s existing quotient-familial math (no duplication).
- **J4-S3** (M) *Per-line method resolution* — override → treaty default → credit-method fallback.
- **J4-S4/S5** (M/M) *Box mapping* for 2042 (salary + investment-income boxes), 2047, 3916 — representative box codes, disclosed as unverified.
- **J4-S6** (S) *Validation* (`validate_filing_inputs` — missing residency, undeclared-account foreign income, missing documents).

### Feature J5 — `FilingSnapshot` compute/validate/lock
- **J5-S1** (L) *Compute endpoint* — upserts a JSONB snapshot from Epic I's estimate + Feature J4's mapping; 409s if locked.
- **J5-S2/S3** (S/S) *Stable read + validate* endpoints.
- **J5-S4** (S) *Lock/unlock* — a direct lock endpoint was added (not deferred entirely to J6's generate-pdf convenience) so locking is testable independently.

### Feature J6 — Cerfa-style PDF generation ⚠️ *highest-risk feature, built smoothly*
- **J6-S1** (XL) *Box-layout data + generic `reportlab` renderer* — fixed grid for 2042, dynamic per-line layouts for 2047/3916.
- **J6-S2** (M) *Generate-pdf endpoint* — single form or a zipped bundle of all three.
- **J6-S3** (S) *Facsimile disclaimer footer* on every generated page.

### Feature J7 — Frontend wizard
- **J7-S1** (M) *`StepIndicator`* — the app's first reusable numbered-progress component.
- **J7-S2-S6** — built as **5 steps** (Residency / ForeignIncome+equity-comp / ForeignAccounts / Deductions&Credits / Summary&Validation): the planned "income sources" and "foreign income" wizard stages share identical upload mechanics and were consolidated into one `ForeignIncomeStep` component.
- **J7-S7/S8** (S/S) *Page assembly + i18n* (96 FR/EN keys, parity verified programmatically).
- **Verified live in-browser** end-to-end against the real household: full navigation, manual entry create/list/delete, auto-computed credit preview, compute/validate/generate-PDF/recompute all confirmed with real numbers, no console errors.

### Feature J8 — Polish
- **J8-S1** (S) *Optional Dashboard tile* — "Tax filing" KPI linking to `/tax-filing`, mirrors I5-S1.
- **J8-S2** (XS) *Docs housekeeping* — `tax_filing` domain + `pdf`/`parsers` sub-packages added to ARCHITECTURE.md.
- **J8-S3** (S) *Wording pass* — reviewed all new disclaimer/simplification copy (FR+EN); already conservative and explicitly says "not tax advice," no changes needed.
- **J8-S4** *Folded into EPICS.md/PROGRESS.md* (this section).

---

## Phase rollup (see [MVP](./MVP.md))
- **P1 (MVP):** A1,A2 · B1,B2 · C1,C2-S1,C3 · D1 · E1 · F1 · G1 · H1,H2,H3 — *consolidated net worth + real returns + the flagship simulator.*
- **P2:** account archive, batch rollback, recurring expenses, vesting, prepayment, goal feasibility, vacation budget, GDPR export.
- **P3:** price provider, Monte Carlo, future-expense projection, tax-wrapper rules engine.
