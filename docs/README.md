# Ledgerly — Design & Build Spec

A **local-first Personal Finance Decision Platform** for advanced French households (PEA, Assurance Vie, PER/PEE/PERCO, Livret A, CTO, ESOP). Budgeting + investments + debt + scenario simulation + long-term planning — running entirely in Docker on the user's own machine. No bank scraping, privacy-first, decision-oriented.

This `/docs` folder is the complete, implementation-ready specification. A clickable wireframe mockup of every screen lives at [`../wireframes.html`](../wireframes.html).

## Read in this order
1. **[PRD.md](./PRD.md)** — vision, personas, use cases, functional + non-functional requirements.
2. **[EPICS.md](./EPICS.md)** — epics → features → user stories with acceptance criteria & phases.
3. **[ARCHITECTURE.md](./ARCHITECTURE.md)** — stack, modular-monolith design, analytics & simulation engines, folder structure, API examples, data flows.
4. **[DATA_MODEL.md](./DATA_MODEL.md)** — entities, ERD, schema, relationships, integrity rules.
5. **[UX_UI.md](./UX_UI.md)** — screen specs, UX principles, visual language, inspiration.
6. **[SECURITY.md](./SECURITY.md)** — privacy guarantees, encryption, secrets, auth, GDPR.
7. **[DEPLOYMENT.md](./DEPLOYMENT.md)** — one-node `docker compose` deploy, backup/restore, future cloud.
8. **[MVP.md](./MVP.md)** — phased delivery plan (P1 → P3) and build order.

## TL;DR for a code agent
- **Stack:** Next.js + TS + Tailwind/shadcn + ECharts ⟷ FastAPI (Python 3.12) + SQLAlchemy/Alembic ⟷ PostgreSQL 16, behind Caddy, all in Docker.
- **Architecture:** modular monolith; pure tested `core/` for money math (amortization, TWR, XIRR, simulation).
- **MVP target:** consolidated net worth (per person/joint/household) + real TWR/XIRR + invest-vs-prepay simulator, in ~3 weeks.
- **Non-negotiables:** cents not floats; no outbound financial data; CSV/manual import only; GDPR export/erase.

Repository layout, naming conventions, and the API surface are defined in [ARCHITECTURE.md](./ARCHITECTURE.md).
