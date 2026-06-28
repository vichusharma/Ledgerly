# Ledgerly — Data Model

Related: [ARCHITECTURE](./ARCHITECTURE.md) · [PRD](./PRD.md)

Conventions: PK `id BIGINT GENERATED ALWAYS AS IDENTITY`. Money = `NUMERIC(20,4)` (EUR base). All tables carry `created_at`, `updated_at`. Soft-delete via `archived_at` where noted. Flexible per-type metadata in `JSONB`.

---

## 1. Entity-relationship overview (ERD)

```
                         ┌──────────┐
                         │  person  │
                         └────┬─────┘
                              │ owns (via account_owner, with split %)
                              ▼
        ┌───────────────────────────────────────────────┐
        │                  account                        │  type: bank|savings|
        │  (1 row per bank/wrapper/loan container)        │  wrapper|liability
        └───┬───────────────┬──────────────┬─────────────┘
            │1:N            │1:N           │1:1 (if liability)
            ▼               ▼              ▼
     ┌────────────┐  ┌──────────────┐  ┌──────────────┐
     │ transaction│  │investment_lot│  │   loan       │
     └─────┬──────┘  └──────┬───────┘  └──────┬───────┘
           │N:1            │N:1               │1:N
           ▼               ▼                  ▼
     ┌──────────┐    ┌────────────┐    ┌──────────────────┐
     │ category │    │ instrument │    │ amortization_row │ (generated/cached)
     └──────────┘    └─────┬──────┘    └──────────────────┘
                           │1:N
                           ▼
                     ┌────────────┐
                     │   price    │ (instrument_id, date, close)
                     └────────────┘

   ┌──────────────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────┐
   │ account_snapshot │     │  goal    │     │ scenario │────►│scenario_result│
   │ (month-end value)│     └──────────┘     └──────────┘     └──────────────┘
   └──────────────────┘
   ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │  rule    │  │ import_batch │  │ travel_budget│  │vesting_grant │
   └──────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 2. Core entities

### person
| col | type | notes |
|-----|------|-------|
| id | PK | |
| display_name | text | "Antoine" |
| role | text | `self` \| `spouse` |
| is_active | bool | |

### account
The container. One row per bank account, per wrapper (one PEA = one account), or per liability.
| col | type | notes |
|-----|------|-------|
| id | PK | |
| name | text | "BoursoBank PEA" |
| institution | text | bank/broker/insurer name |
| type | enum | `bank` \| `savings` \| `wrapper` \| `liability` |
| wrapper_kind | enum null | `pea` \| `pea_pme` \| `av` \| `per` \| `pero` \| `perco` \| `pee` \| `cto` \| `livret_a` \| `ldds` \| `esop` |
| currency | char(3) | default `EUR` |
| metadata | jsonb | wrapper rules: `{opened_at, av_8y_date, pea_5y_date}` |
| archived_at | ts null | |

### account_owner  *(resolves joint ownership & splits)*
| col | type | notes |
|-----|------|-------|
| account_id | FK account | |
| person_id | FK person | |
| ownership_pct | numeric(5,2) | rows per account sum to 100 |
| PK | (account_id, person_id) | |

> A **joint** account = two `account_owner` rows (e.g., 50/50). All scope-based reporting multiplies account values by `ownership_pct` for per-person views; household sums raw.

### category
| col | type | notes |
|-----|------|-------|
| id | PK | |
| parent_id | FK category null | hierarchy: Utilities → Electricity |
| name | text | |
| kind | enum | `expense` \| `income` \| `transfer` |

### transaction
| col | type | notes |
|-----|------|-------|
| id | PK | |
| account_id | FK account | |
| booked_at | date | |
| amount | numeric(20,4) | sign: − expense, + income |
| description | text | raw from CSV |
| category_id | FK category null | |
| import_batch_id | FK import_batch null | for rollback |
| dedup_hash | char(64) | unique per account |
| split_parent_id | FK transaction null | for split lines |
| metadata | jsonb | |

### rule  *(auto-categorization)*
| col | type | notes |
|-----|------|-------|
| id | PK | match_type `regex`\|`contains`; pattern text; category_id FK; priority int |

### import_batch
| col | type | notes |
|-----|------|-------|
| id | PK | account_id FK; filename; mapping jsonb; row_count; duplicate_count; created_at |

---

## 3. Investments

### instrument
| col | type | notes |
|-----|------|-------|
| id | PK | |
| isin | text null | unique |
| ticker | text null | |
| name | text | |
| asset_class | enum | `equity` \| `bond` \| `etf` \| `fund` \| `cash` \| `real_estate` \| `other` |
| region | enum | `fr` \| `eu` \| `us` \| `world` \| `em` \| `other` |
| currency | char(3) | |

### investment_lot  *(the cashflow source for TWR/XIRR)*
| col | type | notes |
|-----|------|-------|
| id | PK | |
| account_id | FK account | the wrapper |
| instrument_id | FK instrument null | null for pure cash contributions |
| type | enum | `buy` \| `sell` \| `dividend` \| `contribution` \| `withdrawal` \| `fee` \| `interest` |
| trade_at | date | |
| quantity | numeric(20,6) | |
| price | numeric(20,6) | per unit, in instrument currency |
| amount | numeric(20,4) | signed cash effect in EUR (fx-converted) |
| fee | numeric(20,4) | |

> **Holdings** are derived (Σ buy−sell quantity per instrument). **Cashflows** for XIRR = external flows (`contribution`/`withdrawal`); TWR sub-periods split at these.

### price
| col | type | notes |
|-----|------|-------|
| instrument_id | FK | |
| date | date | |
| close | numeric(20,6) | EOD |
| PK | (instrument_id, date) | |

### vesting_grant  *(ESOP/RSU)*
| col | type | notes |
|-----|------|-------|
| id | PK | account_id FK (esop); instrument_id FK; grant_date; total_qty; schedule jsonb `[{date, qty}]`; strike numeric null (options) |

---

## 4. Liabilities

### loan
| col | type | notes |
|-----|------|-------|
| id | PK | |
| account_id | FK account (liability) | |
| kind | enum | `mortgage` \| `car` \| `other` |
| principal | numeric(20,4) | original |
| annual_rate | numeric(7,5) | nominal |
| term_months | int | |
| start_date | date | |
| payment_day | int | |
| insurance_monthly | numeric(20,4) null | assurance emprunteur |
| method | enum | `constant_payment` (EMI) \| `constant_amortization` |

### amortization_row  *(generated; cache of the schedule)*
| col | type | notes |
|-----|------|-------|
| loan_id | FK loan | |
| period | int | 1..term |
| due_date | date | |
| payment | numeric(20,4) | |
| interest | numeric(20,4) | |
| principal_paid | numeric(20,4) | |
| balance | numeric(20,4) | remaining capital |
| PK | (loan_id, period) | |

> Prepayments insert an `extra_principal` event and trigger schedule recompute (term- or payment-reduction mode).

---

## 5. Analytics, snapshots & planning

### account_snapshot  *(net-worth history)*
| col | type | notes |
|-----|------|-------|
| account_id | FK | |
| as_of | date | month-end |
| value | numeric(20,4) | bank=balance; wrapper=Σ holdings×price; loan=−remaining capital |
| PK | (account_id, as_of) | |

### goal
| col | type | notes |
|-----|------|-------|
| id | PK | name; kind `fi`\|`payoff`\|`portfolio`\|`custom`; target_amount; target_date; scope enum; baseline_amount |

### scenario
| col | type | notes |
|-----|------|-------|
| id | PK | name; kind `invest_vs_prepay`\|`goal_feasibility`; params jsonb (horizon, lump_sum, monthly, mortgage_id, returns{low,base,high}) |

### scenario_result  *(cached run output)*
| col | type | notes |
|-----|------|-------|
| id | PK | scenario_id FK; run_at; result jsonb (per-return paths, delta[], breakeven_month, interpretation) |

### travel_budget
| col | type | notes |
|-----|------|-------|
| id | PK | name; start_date; end_date; planned_total; line_items jsonb `[{label, planned}]`; tag (links actual transactions) |

---

## 6. Auth & ops

### app_user
| col | type | notes |
|-----|------|-------|
| id | PK | single household; username; password_hash (argon2id); created_at; last_login_at |

### setting
| col | type | notes |
|-----|------|-------|
| key | text PK | e.g., `base_currency`, `target_allocation`, `price_provider_enabled` |
| value | jsonb | |

---

## 7. Derived quantities (not stored, computed in `core/`)
- **Holdings** = Σ(`buy`−`sell`) qty per (account, instrument).
- **Market value** = holdings × latest `price`.
- **Net worth (scope)** = Σ account values × ownership_pct (per scope) − Σ loan balances × ownership_pct.
- **TWR / XIRR** = from `investment_lot` cashflows + `price` history (see [ARCHITECTURE §4](./ARCHITECTURE.md)).
- **Allocation drift** = actual class% − `setting.target_allocation`.

## 8. Integrity rules
- `account_owner.ownership_pct` per account sums to 100 (DB trigger/check).
- `transaction.dedup_hash` unique per `account_id`.
- Money columns `NOT NULL DEFAULT 0`; never float.
- Deleting an `import_batch` cascades to its transactions (rollback).
- `price (instrument_id, date)` unique; snapshots `(account_id, as_of)` unique.
