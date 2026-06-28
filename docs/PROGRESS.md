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
