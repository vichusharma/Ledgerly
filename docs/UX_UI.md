# Ledgerly — UX / UI Design

Related: [wireframes.html](../wireframes.html) (interactive mockup) · [ARCHITECTURE §5](./ARCHITECTURE.md) · [EPICS](./EPICS.md)

---

## 1. UX principles
1. **Every screen answers a question.** Dashboard → "How am I doing?"; Scenarios → "What should I do?". No screen is a passive data dump.
2. **Decision over data.** Lead with the insight (TWR, breakeven, drift), relegate raw rows to secondary views.
3. **Speed = trust.** Linear-grade keyboard nav: a **⌘K command palette** jumps anywhere and runs actions ("Import CSV", "New scenario"). Sub-second transitions.
4. **Calm, minimal, Apple-grade.** Lots of whitespace, one accent color, restrained typography, content-first. No chart-junk.
5. **Progressive disclosure.** Power features (lot editing, vesting schedules) are one click deeper than the headline numbers.
6. **Scope is always visible.** A persistent **Self / Spouse / Joint / Household** toggle in the top bar reframes every number; the active scope is never ambiguous.
7. **Honest numbers.** Show methodology on hover (what TWR vs XIRR mean), mark estimated/stale prices, never imply false precision.

## 2. Visual language
- **Inspiration:** Finary (wealth consolidation & allocation visuals), Linear (speed, command palette, density), Notion (calm typography, clean tables), Copilot Money / Monarch (expense UX).
- **Type:** Inter / SF-style system stack. Tabular figures for all money (`font-variant-numeric: tabular-nums`).
- **Color:** neutral slate canvas; single accent (deep indigo/emerald). Semantic: green=gain, red=loss/debt, amber=drift/warning. Dark mode first-class.
- **Money formatting:** `1 234,56 €` (fr-FR), thin-space thousands, sign-aware coloring.
- **Charts:** ECharts for net-worth area, allocation donut/treemap, scenario lines, amortization stacked bars; Recharts for small KPI sparklines.
- **Density:** comfortable on dashboard, compact tables for transactions/lots.

## 3. Layout system
Persistent **left sidebar** (collapsible) + **top bar** (scope toggle, date range, ⌘K, profile). Content is a responsive 12-col grid; KPI cards row → primary chart → secondary detail. Mobile/tablet: sidebar collapses to icons, cards stack.

---

## 4. Screen specifications

### S1 — Dashboard ("How am I doing?")
- **Top KPI row:** Net Worth (with Δ vs last month), Total Assets, Total Liabilities, Savings Rate.
- **Hero:** Net-worth time-series area chart (scope-aware, range selector 1M/6M/1Y/All).
- **Secondary:** Asset-allocation donut (click → Portfolio), Top expense categories (month), Goal progress mini-bars, Upcoming loan payments.
- **Actions:** ⌘K, "Import CSV", "Add snapshot".

### S2 — Portfolio ("What do I own and what's my real return?")
- KPI: Portfolio Value, **TWR**, **XIRR**, Contributions vs Growth split.
- Wrapper tabs: All / PEA / AV / PER / PEE / CTO / Livret A — each with its rules badge (e.g., "PEA · 5y clock: 3y left").
- Holdings table: instrument, class, qty, price, value, weight, unrealized P/L.
- **Allocation & drift** panel: actual vs target by class/region/currency, drift bars, "Rebalance" hint.
- Performance chart: value vs contributions over time.

### S3 — Debt ("What do I owe and what does it cost?")
- KPI per loan: Remaining Capital, Rate, Interest Paid YTD, Payoff Date.
- Amortization chart: stacked principal/interest over time + remaining-balance line.
- Schedule table (paginated): period, due date, payment, interest, principal, balance.
- **"Prepay / simulate" CTA** → jumps to Scenarios pre-filled with this loan.

### S4 — Expenses ("Where does the money go?")
- Month selector + category treemap/bar.
- Transactions table: date, description, category (inline editable), amount, account; bulk-categorize; rule-create from a row.
- Recurring/expected panel: matched vs missing this month.
- Budget-vs-actual strip for the active month.

### S5 — Scenarios ("What should I do?") — flagship
- **Invest vs Prepay** builder: inputs (lump sum, monthly, horizon, loan picker, low/base/high returns).
- Result: dual line chart (invest path vs prepay path) per return scenario; **breakeven marker**; delta-at-horizon; interest-saved figure.
- Plain-language **interpretation** banner ("At 5%, investing wins after month 58").
- Save scenario; **compare** saved scenarios side-by-side.

### S6 — Goals ("Am I on track?")
- Goal cards: target, current, progress %, projected date, on/off-track chip.
- FI goal: FI number, current coverage, projected FI date, required-return-to-hit.
- Add/edit goal modal.

### S7 — Accounts & Household
- Account list grouped by person/joint; type & wrapper badges; balances; archive.
- Ownership-split editor (per-account % per person).
- Person management (self/spouse).

### S8 — Import / Data
- CSV upload → column-mapping UI (auto-detected, saved per institution) → dedup + auto-categorize preview → confirm.
- Price import (ISIN, date, close). Import-batch history with rollback.

### S9 — Settings
- Target allocation editor, base currency, i18n (EN/FR), price-provider toggle (off by default), backup/restore, **GDPR export & erase**, security (password, recovery codes).

---

## 5. Key interaction patterns
- **⌘K command palette:** navigate + actions (import, new scenario, add transaction, switch scope).
- **Inline edit** for categories and lot fields (no modal where avoidable).
- **Scope toggle** instantly re-queries; remembered in localStorage.
- **Empty states** teach: first-run dashboard guides "Add a person → Add accounts → Import CSV → See net worth".
- **Hover methodology** tooltips on TWR/XIRR/drift.

## 6. Accessibility
WCAG AA contrast, full keyboard operability (Radix primitives), focus-visible rings, screen-reader labels on charts (data table fallback), no color-only signaling (icons + sign).

## 7. Screen → wireframe map
All nine screens are rendered as a clickable mockup in **[../wireframes.html](../wireframes.html)**. The code agent should mirror that layout, component hierarchy, and the scope-toggle/command-palette shell.
