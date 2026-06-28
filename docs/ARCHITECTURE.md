# Ledgerly — Technical Architecture

Related: [PRD](./PRD.md) · [DATA_MODEL](./DATA_MODEL.md) · [SECURITY](./SECURITY.md) · [DEPLOYMENT](./DEPLOYMENT.md)

---

## 1. Architecture principles
1. **Local-first modular monolith.** One deployable backend, internally split into domain modules with clean boundaries — extractable into services *only if* ever needed. No premature microservices.
2. **Deterministic financial core.** All money math (amortization, TWR, XIRR, simulation) lives in a pure, side-effect-free `core` package that is unit-tested against golden datasets. No DB or HTTP in the math.
3. **Contract-first.** Backend emits OpenAPI; the frontend consumes a generated typed client. The contract is the source of truth.
4. **Privacy by construction.** The only optional egress is a price provider, isolated behind one interface, disabled by default, and physically incapable of sending holdings.
5. **Cents, not floats.** Money is `NUMERIC(20,4)` in Postgres and `Decimal` in Python end-to-end.

---

## 2. Recommended stack (decided)

| Layer | Choice | Why |
|-------|--------|-----|
| **Frontend** | **Next.js 14 (App Router) + React 18 + TypeScript** | SSR/streaming for fast dashboards, file-based routing, great DX, runs in one container |
| UI kit | **Tailwind CSS + shadcn/ui (Radix)** | Apple-grade minimal UI fast; accessible primitives |
| Charts | **ECharts** (heavy/financial: candles, time series, allocation) + **Recharts** (simple cards) | ECharts handles large series & financial chart types; Recharts for quick KPI charts |
| State/data | **TanStack Query** + generated **OpenAPI TS client** | Caching, typed calls, no hand-written fetch |
| **Backend** | **Python 3.12 + FastAPI** | Async, Pydantic v2 typing, OpenAPI for free, perfect for analytical/numeric workloads with pandas/numpy |
| Validation | **Pydantic v2** | Shared schema = API contract |
| ORM/migrations | **SQLAlchemy 2.0 + Alembic** | Mature, typed, explicit migrations |
| Numeric | **numpy, pandas, scipy** (XIRR via Newton/Brent), **numpy-financial** | Battle-tested math |
| Tasks | **APScheduler** (in-process) → **Celery/Redis** only if needed | Month-end snapshot & optional price fetch; keep simple |
| **Database** | **PostgreSQL 16** | Window functions, `NUMERIC`, `pgcrypto`, JSONB for flexible metadata |
| Cache (opt) | **Redis** | Memoize TWR/XIRR; rate-limit; sessions. Optional in MVP |
| Auth | Argon2id (`argon2-cffi`) + JWT/session cookie | Local single-household auth |
| Reverse proxy | **Caddy** | Automatic local TLS, simple config |
| Packaging | **Docker + docker compose** | One-node `up` (see [DEPLOYMENT](./DEPLOYMENT.md)) |

> *Node/NestJS alternative was considered.* FastAPI wins here because the product's value is **financial analytics & simulation** — the numeric ecosystem (numpy/pandas/scipy/numpy-financial) makes TWR/XIRR/Monte-Carlo dramatically simpler and faster to get correct than in Node.

---

## 3. System context (C4 level 1)

```
                         ┌──────────────────────────────────────────┐
                         │           USER'S MACHINE (Docker)         │
   ┌──────────┐   HTTPS  │  ┌─────────┐   ┌──────────┐   ┌────────┐  │
   │ Browser  │◄────────►│  │  Caddy  │──►│ Next.js  │   │ Redis  │  │
   │ (SPA/SSR)│  (TLS)   │  │ (proxy) │   │ (web)    │   │ (opt)  │  │
   └──────────┘          │  └────┬────┘   └────┬─────┘   └───┬────┘  │
                         │       │  /api       │ SSR fetch    │       │
                         │       ▼             ▼              │       │
                         │  ┌─────────────────────────────┐  │       │
                         │  │     FastAPI (backend)        │◄─┘       │
                         │  │  api · domains · core math   │          │
                         │  └───────────────┬─────────────┘          │
                         │                  ▼                        │
                         │           ┌────────────┐                  │
                         │           │ PostgreSQL │ (encrypted vol)  │
                         │           └────────────┘                  │
                         └────────────────────────────────────────── ┘
        Optional, OFF by default:  Backend ──► Price provider (prices only, no holdings)
```

No user financial data ever leaves the box. See [SECURITY](./SECURITY.md).

---

## 4. Backend internal structure (C4 level 2 — components)

A **modular monolith**: each domain is a self-contained module exposing a service interface; the `core` package holds pure math; the `api` layer is thin (HTTP → service).

```
┌──────────────────────────── FastAPI app ─────────────────────────────┐
│  api/        (routers, request/response schemas, auth dependency)     │
│      │ depends on                                                     │
│      ▼                                                                │
│  domains/    accounts │ transactions │ investments │ liabilities │   │
│              networth │ scenarios    │ planning     │ imports     │   │
│      │ each = service.py + repository.py + models.py + schemas.py     │
│      ▼ call                                                           │
│  core/       money │ amortization │ performance(twr,xirr) │          │
│              allocation │ simulation │ projection   (PURE, tested)    │
│      ▼ persist via                                                    │
│  infra/      db (SQLAlchemy) │ migrations │ security(crypto,auth) │   │
│              scheduler │ price_provider(iface) │ settings            │
└───────────────────────────────────────────────────────────────────────┘
```

**Dependency rule:** `api → domains → core`; `domains → infra`. `core` depends on nothing (no DB, no FastAPI). This keeps the math testable and the modules swappable.

### Analytics engine (`core/performance`, `core/allocation`)
- **TWR (Time-Weighted Return):** chain sub-period returns split at every external cashflow (contribution/withdrawal), removing the effect of *when* money was added. `TWR = Π(1 + r_i) − 1`.
- **XIRR (Money-Weighted):** solve `Σ CF_t / (1+rate)^((t−t0)/365) = 0` via Newton's method with Brent fallback for robustness. Inputs: dated cashflows incl. current value as final positive flow.
- **Allocation & drift:** group current valuations by `asset_class/region/currency/wrapper`; compare to a stored target; drift = actual% − target%.
- All functions are **pure**: `(cashflows, prices) → numbers`. Golden tests pin known results.

### Simulation engine (`core/simulation`, `core/projection`)
- **Invest-vs-prepay:** two parallel deterministic projections over `N` months:
  - *Prepay path:* extra €X reduces mortgage principal → recompute amortization → interest saved; remaining cash invested at return `r`.
  - *Invest path:* €X invested at return `r`; mortgage runs to schedule.
  - Output: monthly net-worth for each path, **delta**, and **breakeven month** (where invest path overtakes prepay path). Run for `r ∈ {low, base, high}`.
- **Goal feasibility:** project contributions + returns to target date; report projected value vs. goal and implied required return.
- **Monte Carlo (P3):** sample annual returns ~ N(μ,σ); 1,000+ paths; report p10/p50/p90 bands.

---

## 5. Frontend structure

```
web/
  app/                       # Next.js App Router
    (dashboard)/page.tsx     # Net-worth dashboard
    portfolio/page.tsx
    debt/page.tsx
    expenses/page.tsx
    scenarios/page.tsx
    goals/page.tsx
    accounts/page.tsx
    import/page.tsx
    settings/page.tsx
    layout.tsx               # app shell: sidebar + command palette + person/household toggle
  components/                # ui/ (shadcn) + charts/ (ECharts wrappers) + finance/ (KPI cards, NetWorthChart...)
  lib/
    api/                     # generated OpenAPI client + TanStack Query hooks
    format/                  # EUR/date/i18n (fr-FR, en)
    hooks/
  styles/
```

**Person/Household toggle** is a global context that adds a `scope` param to every analytics query (self | spouse | joint | household).

---

## 6. Repository layout (monorepo)

```
ledgerly/
├─ docker-compose.yml            # caddy, web, api, db, (redis)
├─ Caddyfile
├─ .env.example
├─ docs/                         # this spec
├─ web/                          # Next.js frontend (see §5)
├─ api/                          # FastAPI backend
│  ├─ pyproject.toml
│  ├─ app/
│  │  ├─ main.py                 # FastAPI factory, routers, middleware
│  │  ├─ api/                    # routers + http schemas + deps (auth)
│  │  ├─ domains/                # accounts, transactions, investments,
│  │  │                          #   liabilities, networth, scenarios,
│  │  │                          #   planning, imports
│  │  ├─ core/                   # pure math: money, amortization,
│  │  │                          #   performance, allocation, simulation
│  │  ├─ infra/                  # db, security, scheduler, price_provider, settings
│  │  └─ tests/                  # unit (core golden tests) + integration
│  └─ alembic/                   # migrations
└─ scripts/                      # backup.sh, restore.sh, seed.py, gen_client.sh
```

### Naming conventions
- **Python:** modules/functions `snake_case`, classes `PascalCase`, Pydantic schemas suffixed `…In` / `…Out` (e.g., `AccountCreateIn`, `AccountOut`). DB tables plural `snake_case` (`investment_lots`).
- **TypeScript:** components `PascalCase`, hooks `useCamelCase`, files match export. API hooks `useNetWorth`, `useRunScenario`.
- **REST:** plural nouns, kebab where multi-word: `/api/v1/investment-lots`. Actions as sub-resources: `POST /scenarios/{id}/run`.
- **Money fields** always suffixed with currency intent: `amount_cents` or `amount` (NUMERIC) — never ambiguous floats.

---

## 7. API surface (representative, `/api/v1`)

```
POST /auth/login                 → {token}            # argon2id, sets httpOnly cookie
GET  /persons                    → [Person]
POST /accounts                   → Account
GET  /accounts?scope=household   → [Account]

POST /imports/csv                # multipart: file + mapping_id  → ImportBatch (counts, dupes)
POST /transactions               → Transaction
PATCH /transactions/{id}         # categorize / split
POST /rules                      → Rule            # /EDF/ → Electricity

POST /instruments                → Instrument      # ISIN, class, region, currency
POST /investment-lots            → Lot             # buy/sell/dividend/contribution/fee
POST /prices/import              # CSV: isin,date,close
GET  /portfolio/performance?scope=&wrapper=  → {twr, xirr, contributions, growth, series[]}
GET  /portfolio/allocation?scope=            → {byClass[], byRegion[], drift[]}

POST /liabilities                → Loan
GET  /liabilities/{id}/schedule  → [AmortRow]      # date, payment, interest, principal, balance

GET  /networth?scope=&from=&to=  → {current, series[]}

POST /scenarios                  → Scenario
POST /scenarios/{id}/run         → ScenarioResult   # paths, delta[], breakeven_month
GET  /scenarios?compare=a,b      → [ScenarioResult]

POST /goals                      → Goal
GET  /goals/{id}/progress        → {pct, projectedDate, onTrack}

GET  /export                     → application/zip   # GDPR full export
DELETE /account/data             → 204               # GDPR erase
```

### Example — run invest-vs-prepay scenario
```http
POST /api/v1/scenarios/42/run
Content-Type: application/json

{
  "horizon_months": 240,
  "lump_sum": 20000,
  "monthly": 0,
  "mortgage_id": 7,
  "returns": { "low": 0.02, "base": 0.05, "high": 0.08 }
}
```
```json
{
  "scenario_id": 42,
  "currency": "EUR",
  "results": {
    "base": {
      "invest_net_worth_end": 412300.55,
      "prepay_net_worth_end": 398110.20,
      "delta_end": 14190.35,
      "breakeven_month": 58,
      "interest_saved_if_prepay": 21840.00,
      "series": [ { "month": 1, "invest": 100.0, "prepay": 95.0 }, "…" ]
    },
    "low":  { "delta_end": -3200.10, "breakeven_month": null, "…": "…" },
    "high": { "delta_end": 41280.90, "breakeven_month": 31,  "…": "…" }
  },
  "interpretation": "At base (5%) investing beats prepaying after month 58; at low (2%) prepaying wins."
}
```

---

## 8. Key data flows

### 8.1 CSV import → categorized transactions
```
User uploads CSV ─► POST /imports/csv (file + mapping_id)
   │
   ├─ imports.service: parse rows → normalize (Decimal, date) 
   ├─ dedup: sha256(account_id|date|amount|desc) vs existing
   ├─ apply rules: regex(desc) → category_id
   └─ persist ImportBatch + Transactions (atomic)
   ▼
Return {imported, duplicates, uncategorized}  ─► UI shows review queue
```

### 8.2 Net-worth time series
```
Month-end scheduler ─► snapshot each account balance
   (bank=last balance; investment=Σ lots×price@date; loan=remaining capital)
   ▼ store AccountSnapshot rows
GET /networth ─► sum snapshots by scope & ownership split ─► series ─► ECharts
```

### 8.3 Portfolio performance
```
GET /portfolio/performance
   ├─ load lots (cashflows) + price history per instrument
   ├─ core.performance.twr(periods split at cashflows)
   ├─ core.performance.xirr(dated cashflows + current value)
   └─ cache (Redis) keyed by (scope,wrapper,price_version)
   ▼ {twr, xirr, contributions vs growth, series}
```

---

## 9. Cross-cutting concerns
- **Caching:** materialized `AccountSnapshot` for history; Redis memoization for TWR/XIRR invalidated on new lots/prices (`price_version` counter).
- **Migrations:** Alembic, forward-only, reviewed; seed script for demo data.
- **Observability (local):** structured JSON logs, `/health`, request timing; no external telemetry.
- **Testing:** `core/` golden tests (amortization, TWR, XIRR vs. known answers); domain integration tests on a throwaway Postgres; Playwright smoke test on the web shell.
- **Config:** 12-factor via env + Pydantic `Settings`; secrets via Docker secret files (see [SECURITY](./SECURITY.md)).
