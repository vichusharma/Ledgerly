# Ledgerly — MVP & Delivery Plan

Related: [EPICS](./EPICS.md) · [PRD](./PRD.md). Philosophy: **ship a trustworthy consolidated net worth + the flagship simulator fast**, then layer depth. No overengineering.

Sequencing assumes ~1–2 engineers. Week ranges are effort, not calendar mandates.

---

## Phase 1 — MVP (≈ Weeks 1–3): "See everything + the one decision that matters"
**Outcome:** a French household imports CSVs, enters wrappers + a mortgage, and within 30 minutes sees consolidated net worth, real TWR/XIRR, and runs *invest-vs-prepay*.

Scope (P1 stories from [EPICS](./EPICS.md)):
- **Foundation:** Docker compose stack, Postgres + Alembic, app shell + sidebar + ⌘K, argon2id auth, EN/FR + EUR formatting, OpenAPI typed client. (H1, H2, H3)
- **Household & accounts:** persons, accounts, ownership split, scope toggle. (A1, A2)
- **Transactions:** mapped CSV import + dedup, hierarchical categories, rule-based auto-categorize, manual entry. (B1, B2)
- **Investments:** wrapper accounts (PEA/AV/PER/PEE/Livret A/CTO/ESOP shell), lot transactions, instruments, **manual/CSV price import**, **TWR + XIRR**, allocation + drift. (C1, C2-S1, C3-S1/S2)
- **Liabilities:** model loan + full amortization, debt view. (D1-S1/S2)
- **Net worth:** current + month-end snapshots + time series. (E1)
- **Scenario:** invest-vs-prepay simulator (low/base/high) + save/compare. (F1-S1/S2)
- **Goals:** create + track a goal (FI number). (G1)
- **Security/ops:** TLS, secrets via Docker secrets, backup/restore. (H1, H2-S2)

**Definition of done:** dashboard < 1.5s on demo data; TWR/XIRR pass golden tests; net worth correct per scope; one scenario produces a breakeven; `docker compose up` works clean.

**Explicitly deferred from MVP:** vesting detail, prepayment recompute, recurring-expense reconciliation, vacation budget, Monte Carlo, price provider, tax rules.

---

## Phase 2 — Depth & household life (≈ Weeks 4–7): "Make it livable"
- Recurring/expected expenses + reconciliation. (B2-S4)
- Import-batch rollback; account archive. (B1-S3, A2-S3)
- ESOP/RSU vesting schedules (vested/unvested). (C3-S3)
- Loan prepayment recompute (term/payment reduction). (D1-S3)
- Goal feasibility simulation (projected date, required return). (F2-S1)
- Vacation/travel budget with plan-vs-actual. (G2-S1)
- GDPR export + erase. (H1-S3)
- Per-person PIN for spouse views (optional).

---

## Phase 3 — Intelligence & polish (≈ Weeks 8+): "Decision superpowers"
- Optional pluggable **price provider** (off by default, prices only). (C2-S2)
- **Monte Carlo** simulation with percentile bands. (F1-S3)
- Future-expense projection feeding net-worth forecast. (G2-S2)
- **Tax-wrapper rules engine** (PEA 5y clock, AV 8y, PER deductibility hints). (FR-INV-8)
- Redis caching for heavy analytics; performance hardening.
- Optional remote access (Tailscale) + cloud-VM deploy guide.

---

## Cross-phase guardrails
- **Build the `core/` math first and test it against golden datasets** before wiring UI — amortization, TWR, XIRR are the trust foundation.
- Each phase ends with: passing golden + integration tests, a clean `docker compose up`, and a backup/restore rehearsal.
- Resist scope creep: anything not advancing "consolidated net worth" or "better decisions" waits.

---

## Suggested build order within Phase 1 (dependency-aware)
1. Stack + auth + shell + migrations (H2, H1, H3).
2. Persons/accounts/ownership + scope (A1, A2).
3. `core/` math: amortization, TWR, XIRR + golden tests.
4. Instruments + lots + price import → portfolio performance & allocation (C1, C2-S1, C3).
5. Loans + amortization + debt view (D1).
6. Transactions: CSV import + categories + rules (B1, B2).
7. Net-worth snapshots + dashboard (E1).
8. Invest-vs-prepay scenario + save/compare (F1).
9. Goals (G1) + backup/restore + polish.
