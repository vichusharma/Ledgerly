# Ledgerly — Backlog: French Expat Tax Filing Module

> Working backlog for a not-yet-started feature, kept separate from [EPICS.md](./EPICS.md)/[PROGRESS.md](./PROGRESS.md) (which reflect the completed A–I epics) until this one is built — at that point its stories should be folded into those two files, the same way Epic I's stories were. Structured the same way: Epic → Feature → Story, `Given/When/Then` acceptance criteria, story points (XS=1, S=2, M=3, L=5, XL=8).
>
> Planned via `/plan` on 2026-07-07 (research: 2 Explore agents on backend/frontend patterns + 1 Plan agent for the detailed design; see `SESSION_SUMMARY.md` for the session log and the decisions behind each choice below). Replaces this file's prior content (Epic I), which is now built and folded into `EPICS.md`/`PROGRESS.md`.

## Context & confirmed decisions

Epic I already estimates a French household's income tax (salary + investment income, barème progressif, quotient familial, régime des impatriés) via `TaxService.get_tax_estimate()`. That's a live *estimate*, not a *filing* — it never touches foreign-source income, foreign bank account declarations, or RSU/ESPP equity comp, and produces no document usable at filing time. Epic J adds that layer, for the case that matches the household's own real situation: **a foreigner who is a French tax resident** (e.g. the household's primary member, already using the impatriate regime) who also has foreign-source income and foreign bank accounts back home that must be declared alongside the main French return — Forms 2042 (main return), 2047 (foreign-source income), 3916 (foreign bank accounts).

Three scope decisions were confirmed with the user before designing (asked via `AskUserQuestion`):
1. **PDF output**: an attempted **facsimile of the official Cerfa 2042/2047/3916 layouts** (box grid, real box codes, official section numbering), not just a plain values-worksheet — the more ambitious of the two options offered. Caveat baked into the design: a true pixel-identical copy of DGFiP's actual template isn't legally reproducible (copyrighted, changes yearly) — "facsimile" means a *programmatically-drawn structural recreation* via `reportlab`, not an overlay on a scanned government PDF. Every generated page carries a disclaimer footer saying so.
2. **Document retention**: original uploaded source documents (RSU vesting statements, ESPP confirmations, foreign dividend/bank statements) are **retained as an encrypted audit trail** — a genuinely new capability, chosen over the "structured data only, discard the PDF" option that matches every existing parser in the app today (payslips, PDF valuations, bank statements all currently parse transiently and discard the bytes).
3. **Population**: a foreigner tax-resident in France, filing *as a French resident* — this builds directly on Epic I's impatriate work, not a "French citizen living abroad" regime (different forms, would not reuse Epic I).

### Ground-truth findings that shape this backlog (verified against the repo, 2026-07-07)
- `Person` (`api/app/domains/accounts/models.py`) already carries Epic I's 3 impatriate columns directly — the established convention is per-individual facts live on `Person` or a new per-person table, not a household-wide one. Residency facts follow this: a new `PersonTaxResidency` table, not more `Person` columns (residency needs ~5 fields, cohesive to this new domain).
- `Account` has no `country_code`/foreign-identity field yet, but does have the `opened_at` precedent (added directly to `Account` in Feature I4) for "extend the existing table with a persistent fact, add a side table only for year-specific facts" — followed here: `country_code` on `Account`, plus a new `ForeignAccountDeclaration` table for 3916's per-tax-year facts (opened/closed this year, masked number).
- `InvestmentLot`'s `LotType` enum already has an unused `vesting` value, and `VestingSchedule` already exists (`investments/models.py`) but has never been wired to any parser or UI (P2, built then dormant) — Epic J is the first real consumer of both.
- `Settings.encryption_key`/`ENCRYPTION_KEY_FILE` (`api/app/infra/settings.py`) already exists, resolved from a Docker secret, but **has zero consumers anywhere in the codebase today** — pure scaffolding. `docs/SECURITY.md` reserves literal Postgres `pgcrypto`/`pgp_sym_encrypt` for "genuinely sensitive secrets," but nothing in the repo calls that either. Epic J implements application-layer AES (via the already-a-dependency `cryptography` lib) keyed from this existing setting — its first real consumer, and functionally equivalent column-level encryption without adding a new DB extension dependency.
- `PlanningService.export_all_data()`/`erase_all_data()` (`api/app/domains/planning/service.py`) are the existing GDPR export/erase implementations — confirmed via direct read that `erase_all_data()`'s hard-coded table list **doesn't even include Epic I's own tables** (`payslips`, `tax_year_configs`, `household_tax_settings`, `household_tax_dependents`) yet. Epic J must add its own new tables to this list, and should flag (not silently fix) the pre-existing Epic I gap alongside it.
- Migrations are linear zero-padded 4-digit ids; latest is `0011_person_date_of_birth`; Epic J continues at `0012`.
- New domain routers/models still require manual registration (`api/app/main.py::create_app()`, `api/alembic/env.py`'s flat import list) — nothing auto-discovers.
- No shared Stepper/Wizard component exists anywhere in the frontend — every multi-step flow (`salary`, `import`) hand-rolls its own `Step` union with no visible numbered-progress UI. Epic J's 6-step wizard is bigger than any existing flow and gets the app's first reusable `StepIndicator` component.

### Documented simplifications (surfaced to the user in the UI, not silently applied)
1. Cerfa "facsimile" is a structural recreation (box codes, section layout) via `reportlab`, not a copy of DGFiP's actual template — disclosed via a footer on every generated page.
2. Box codes mapped from Ledgerly's data (2042/2047/3916) are representative, not verified against the actual current-year DGFiP instructions — must be checked by the user before ever being used for a real filing.
3. `TreatyMetadata` is seeded for a handful of countries only (India, US, UK, Canada, Germany), not all ~120 French tax treaties; any other country defaults to the "crédit d'impôt égal à l'impôt français" method with an explicit `treaty_method_defaulted_unseeded_country` flag.
4. The PFU-vs-barème and foreign-tax-credit approximations inherit every Epic I simplification already disclosed (average-cost gains, household/primary-level election, general-case quotient-familial plafonnement, etc.) since this module calls `TaxService.get_tax_estimate()` rather than re-deriving those numbers.
5. ESPP purchases are modeled as a `buy`-type `InvestmentLot` with two new nullable fields (`fmv_at_acquisition`, `discount_pct`), not a distinct lot type — ordinary-income-at-purchase vs. capital-gain-at-sale splitting is not modeled in this pass.

---

## EPIC J — French Expat Tax Filing Module

### Feature J1 — Residency & per-person tax-filing facts
**Goal:** capture the facts (per-person residency, treaty country default) the rest of the module needs before any filing computation exists.
- **J1-S1** (M) *Per-person residency profile.* Given any household member, when I set their home country, home-country tax ID, and French tax number (numéro fiscal), then it's stored per-person, never household-wide. New `PersonTaxResidency` table, migration `0012_person_tax_residency.py`.
- **J1-S2** (S) *API.* `GET/PUT /tax-filing/residency/{person_id}`.
- **J1-S3** (S) *Wizard residency step.* `web/src/components/tax-filing/ResidencyStep.tsx`, per-person expandable form mirroring `TaxProfileSection`'s `PersonImpatriateRow` pattern.
- **J1-S4** (M) *Treaty metadata reference.* Given a handful of seeded countries, when a foreign-income line references an unseeded country, then it defaults to the credit method and is flagged `treaty_method_defaulted_unseeded_country`. New `TreatyMetadata` table, migration `0013_treaty_metadata.py` (+ seed: India, US, UK, Canada, Germany), `GET /tax-filing/treaties`.

### Feature J2 — Foreign income/account data entry + parsers
**Goal:** get RSU vesting, ESPP purchases, foreign dividends, and foreign bank accounts into the system, mirroring the existing preview→review→confirm parser convention.
- **J2-S1** (L) *RSU vesting statement parser.* Given an RSU vesting statement PDF, when uploaded, then grant date/total shares/cliff-vesting months/grant price/vest event are extracted as an editable candidate. `api/app/domains/tax_filing/parsers/rsu_vesting_parser.py`, modeled on `pdf_payslip_parser.py`. Confirm creates/updates the existing (currently unused) `VestingSchedule` row + one `InvestmentLot(lot_type=vesting)`.
- **J2-S2** (L) *ESPP purchase confirmation parser.* Given an ESPP purchase confirmation, when uploaded, then purchase date/shares/purchase price/FMV/discount % are extracted. `espp_purchase_parser.py`. Confirm creates `InvestmentLot(lot_type=buy, fmv_at_acquisition=..., discount_pct=...)`. New nullable columns via migration `0017_investment_lot_espp_fields.py`.
- **J2-S3** (M) *Foreign dividend statement parser.* `foreign_dividend_statement_parser.py` → `ForeignIncomeDeclaration` candidate (income_type=foreign_dividend).
- **J2-S4** (M) *Foreign bank statement parser.* `foreign_bank_statement_parser.py` → `ForeignAccountDeclaration` candidate (bank name, masked number, country, opened/closed hints).
- **J2-S5** (M) *Confirm flows write structured data + upsert-by-natural-key.* Each confirm endpoint also hands the original bytes to the Feature J3 encryption path (built ahead of this story — see Delivery order).
- **J2-S6** (S) *`Account.country_code`.* Migration `0014_account_country_code.py` + an editable field on the Accounts page (null = France, same fallback convention as `opened_at`).
- **J2-S7** (M) *Manual CRUD.* Full CRUD for `ForeignIncomeDeclaration` (migration `0015_foreign_income_declarations.py`) and `ForeignAccountDeclaration` (migration `0016_foreign_account_declarations.py`) for entries with no source document.
- **J2-S8** (S) *i18n.* New `taxFiling` namespace, parser-step strings, FR+EN.

### Feature J3 — Encrypted document storage
**Goal:** retain original source PDFs as an encrypted audit trail (the confirmed scope decision, a genuinely new capability for this app).
- **J3-S1** (L) *Crypto helper + `TaxDocument` table.* Given a reviewed source PDF, when confirmed, then its bytes are AES-encrypted via new `api/app/infra/document_crypto.py` (keyed from the existing, currently-unused `Settings.encryption_key`/`ENCRYPTION_KEY_FILE`) and stored in `tax_documents.encrypted_content`. Migration `0018_tax_documents.py`. **Build this story before Feature J2's confirm flows**, which depend on it.
- **J3-S2** (M) *Wire every J2 confirm endpoint to J3-S1.*
- **J3-S3** (S) *List + download.* `GET /tax-filing/documents`, `GET /tax-filing/documents/{id}/download` (decrypts, streams, audit-logs the access — never returns ciphertext or logs the raw hash).
- **J3-S4** (S) *Per-document delete.* `DELETE /tax-filing/documents/{id}`; retention note surfaced in `DocumentList.tsx` ("kept for audit purposes, delete anytime").
- **J3-S5** (M) *GDPR wiring.* Extend `PlanningService.export_all_data()` to decrypt and include each `TaxDocument` as a file in the export zip; extend `erase_all_data()`'s table list to cover every new Epic J table — and close the pre-existing gap that Epic I's own tables were never added either.

### Feature J4 — `tax_filing_rules` engine (deductions/credits/treaty)
**Goal:** map the existing tax estimate plus new filing-specific facts onto DGFiP form line items, without duplicating `core/tax.py`'s bracket/quotient math.
- **J4-S1** (L) *Foreign tax credit — credit method.* `api/app/core/tax_filing_rules.py::compute_french_tax_attributable_to_income` (calls `core/tax.compute_quotient_tax` twice: tax(total) − tax(total − income_slice)) — the "crédit d'impôt égal à l'impôt français" amount. Golden-tested.
- **J4-S2** (L) *Exemption avec taux effectif.* `compute_effective_rate_exemption` — foreign income raises the average rate without itself being taxed. Golden-tested.
- **J4-S3** (M) *Per-line method resolution.* `resolve_elimination_method` — per-line override → `TreatyMetadata` default → credit-method fallback + simplification flag.
- **J4-S4** (M) *Box mapping — 2042/2047.* `map_estimate_to_2042_boxes`, `map_investment_income_to_2042_boxes`, `map_foreign_income_to_2047_lines` (representative box codes, flagged unverified per simplification #2).
- **J4-S5** (M) *Box mapping — 3916.* `map_foreign_accounts_to_3916_entries`.
- **J4-S6** (S) *Validation.* `validate_filing_inputs` — missing residency, an undeclared foreign account with a linked foreign dividend, doc-less declarations, etc.

### Feature J5 — Compute/validate endpoints, wired into `TaxService`
**Goal:** a stable, lockable "filing snapshot" per tax year, built on top of Epic I's estimate rather than beside it.
- **J5-S1** (L) *`FilingSnapshot` + compute endpoint.* `POST /tax-filing/compute?year=` calls `TaxService.get_tax_estimate(year, include_investments=True)` + `tax_filing_rules`, upserts a `FilingSnapshot` (JSONB payload), 409s if already locked. Migration `0019_filing_snapshots.py`.
- **J5-S2** (S) *Stable read.* `GET /tax-filing/forms/{year}` — 404 if never computed.
- **J5-S3** (S) *Validate endpoint.* `POST /tax-filing/validate?year=`.
- **J5-S4** (S) *Lock/unlock.* `POST /tax-filing/forms/{year}/unlock`; the normal lock path is `generate-pdf`'s `lock: bool` body param (Feature J6).

### Feature J6 — Cerfa-style PDF generation ⚠️ *most ambitious/highest-risk feature (mirrors Epic I's I4 flag)*
**Goal:** a structural recreation of the 2042/2047/3916 box-grid layout, pre-filled with computed values.
- **J6-S1** (XL) *Box-layout data + generic renderer.* `api/app/domains/tax_filing/pdf/layouts/cerfa_{2042,2047,3916}_layout.py` (position/size/label per box code, so next year's renumbering is a data edit) + one generic `render_box_grid()` `reportlab` renderer reused across all three forms. **Risk**: no official government asset to check the visual bar against — inherently iterative, uncertain work, exactly like Epic I's I4.
- **J6-S2** (M) *Generate-pdf endpoint.* `POST /tax-filing/generate-pdf?year=&form=2042|2047|3916|all` — single form or a bundled zip of all three; reads the locked-or-latest `FilingSnapshot`.
- **J6-S3** (S) *Facsimile disclaimer.* Footer stamped on every generated page: "Document généré par Ledgerly — reproduction structurelle, non un formulaire officiel Cerfa."

### Feature J7 — Frontend wizard
**Goal:** a 6-step guided flow (residency → income sources → foreign income → foreign accounts → deductions/credits → summary/validation), the app's first with visible numbered progress.
- **J7-S1** (M) *`StepIndicator` component.* New shared `web/src/components/ui/StepIndicator.tsx` — numbered circles + connector line, back-navigation only, `brand`/`surface-border` tokens.
- **J7-S2** (M) *ResidencyStep* (Feature J1's UI, listed here for wizard sequencing).
- **J7-S3** (L) *ForeignIncomeStep* — RSU/ESPP/dividend dropzones (per doc type) + manual-row table, its own internal upload→review→confirm sub-flow matching `salary/page.tsx`.
- **J7-S4** (L) *ForeignAccountsStep* — statement dropzone + manual rows referencing existing `Account`s.
- **J7-S5** (M) *DeductionsCreditsStep* — per-line treaty method display/override + computed foreign-tax-credit preview.
- **J7-S6** (L) *SummaryValidationStep* — calls `/validate` + `/compute`, renders the box-code table, Generate-PDF + Lock actions, disclaimer block matching `/tax`'s existing pattern.
- **J7-S7** (S) *Page assembly + nav.* `web/src/app/tax-filing/page.tsx`, `nav.taxFiling` sidebar entry (deviates from the `modules/tax` folder shape originally suggested — this repo's convention is flat `app/<domain>/page.tsx`).
- **J7-S8** (S) *i18n.* `taxFiling` namespace, FR+EN, box captions via `box_${code}` and simplification captions via `simplification_${key}` (same prefix convention as the existing `tax` namespace).

### Feature J8 — Polish
- **J8-S1** (S) *Optional Dashboard tile.* Small "Tax filing" KPI/link on `/dashboard` → `/tax-filing` (mirrors I5-S1).
- **J8-S2** (XS) *Docs housekeeping.* `docs/ARCHITECTURE.md` gains the `tax_filing` domain + `pdf/` sub-package.
- **J8-S3** (S) *Wording pass.* Review every new simplification/disclaimer string (FR+EN) for conservative, non-advice-sounding language, matching Epic I's I5-S3 bar.
- **J8-S4** *Fold into EPICS.md/PROGRESS.md* once built, same as Epic I's precedent; `docs/Backlog.md` gets replaced again for whatever epic comes next.

---

## Delivery order
**J1 → J3(S1–S2, schema+crypto only) → J2 → J3(S3–S5, UI/GDPR) → J4 → J5 → J6 → J7 → J8.** J3's storage schema and crypto helper must exist before J2's parser-confirm flows can persist originals, so those two stories are pulled forward ahead of J2 despite the numbering; J3's list/download/delete/GDPR stories land after, once there's data to view. **J6 (Cerfa PDF facsimile) is the riskiest/most ambitious feature** — building a convincing box-grid recreation with zero official asset to check against is inherently iterative and uncertain, exactly like I4 was for Epic I. **J4 (treaty engine)** is the second-highest-risk item, given the legal-accuracy stakes of foreign-tax-credit modeling — both should get the most review/verification time before the module is used for a real filing.

## Verification (per increment)
- Backend: `docker compose -f docker-compose.test.yml run --rm api-test` (always `... down` after) — all tests green, including new golden tests for `core/tax_filing_rules.py` (mirroring `test_tax.py`'s per-function-class style) and integration tests mirroring `test_tax_estimate_flow.py`'s helper-function pattern.
- Frontend: `npm run type-check` / `next build` clean (watch for the incidental `tsconfig.json` rewrite).
- Manual: upload a real/synthetic RSU/ESPP/foreign-statement PDF through the wizard after J2; generate a PDF for a test year and visually sanity-check the box grid after J6; verify FR+EN throughout. **Box codes and the Cerfa layout must be checked against the actual current-year DGFiP instructions before this is ever used for a real filing** — a disclosed simplification, not a verified fact, same discipline as every Epic I caveat.
