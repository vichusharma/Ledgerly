# Ledgerly — Security & Privacy Design

Related: [PRD §5](./PRD.md) · [DEPLOYMENT](./DEPLOYMENT.md) · [ARCHITECTURE](./ARCHITECTURE.md)

Threat model is unusual for a finance app: **the data never leaves the user's machine**, so the primary adversaries are (a) other processes / users on the host, (b) someone with physical access to the disk/backups, and (c) accidental data egress. We optimize for those.

---

## 1. Privacy guarantees (the product promise)
- **No bank credential scraping.** Ingestion is CSV/manual only (MVP). There is no code path that authenticates to a bank.
- **No outbound financial data.** The only optional egress is the **price provider**, which is: off by default, behind a single interface (`infra/price_provider`), and only ever sends an **ISIN + date** — never balances, holdings, or transactions. A network-egress test in CI asserts no other component opens sockets.
- **GDPR by design:** one-click **full export** (`GET /export` → zip of JSON/CSV) and **hard erase** (`DELETE /account/data`) of all rows. Data minimization: we store only what the user enters.

---

## 2. Authentication & authorization
- Single-household local auth. Password hashed with **Argon2id** (`argon2-cffi`, sensible memory/time cost). No password reset email (local); instead **recovery codes** generated at setup.
- Session = **JWT in an httpOnly, Secure, SameSite=Strict cookie**; short access token + rotating refresh. CSRF protection via double-submit token for state-changing requests.
- Two profiles (self/spouse) share the single login by default; optional per-person PIN can gate spouse-only views (P2). Authorization is coarse — it's one household — but the `scope` param is validated server-side.
- Brute-force: rate-limit `/auth/login` (Redis or in-memory leaky bucket); exponential backoff after 5 failures.

---

## 3. Encryption

### In transit
- **TLS everywhere**, even on localhost. Caddy terminates TLS with a locally-trusted certificate (Caddy's internal CA or `mkcert`). The browser↔Caddy and Caddy↔services hops are HTTPS; service↔service inside the Docker network uses the internal CA.

### At rest
- **Volume encryption** (recommended): the Postgres data volume sits on an encrypted disk (LUKS / FileVault / BitLocker) — documented as a deployment prerequisite.
- **Column-level encryption** for the few genuinely sensitive secrets (e.g., any future provider API key, recovery codes) using `pgcrypto` (`pgp_sym_encrypt`) with a key supplied via Docker secret — *not* the bulk financial tables (which would kill query/analytics performance for marginal benefit given volume encryption already covers them).
- **Backups encrypted:** `scripts/backup.sh` pipes `pg_dump` through `age`/`gpg` symmetric encryption; restore documented.

---

## 4. Secrets management
- All secrets via **Docker secrets** (`/run/secrets/...`) or a root-owned `.env` excluded from git — never baked into images or committed. `.env.example` ships with placeholders.
- Secrets inventory: `POSTGRES_PASSWORD`, `APP_SECRET_KEY` (JWT signing), `PGCRYPTO_KEY` (column encryption), `BACKUP_PASSPHRASE`.
- Key handling warning on first run: **if you lose `PGCRYPTO_KEY`/disk key, encrypted data is unrecoverable** — prompt the user to store recovery codes safely.
- Rotation: documented procedure to re-sign sessions (`APP_SECRET_KEY` rotation invalidates sessions) and re-encrypt columns.

---

## 5. Application hardening
- **Input validation** with Pydantic on every endpoint; reject unexpected fields.
- **SQL injection:** parameterized via SQLAlchemy only; no string-built SQL.
- **File upload safety:** CSV parser streams with size caps, content-type + extension checks, and never `eval`s; price/transaction files validated against a schema before persist.
- **Security headers** (Caddy): HSTS, `X-Content-Type-Options`, `X-Frame-Options: DENY`, strict `Content-Security-Policy` (no inline scripts; self only), `Referrer-Policy: no-referrer`.
- **CORS:** locked to the local web origin only.
- **Dependency hygiene:** `pip-audit` / `npm audit` in CI; pinned lockfiles; minimal base images (`python:3.12-slim`, `node:20-slim`).
- **Least privilege:** containers run as non-root; Postgres not exposed on host (only on the internal Docker network); web/api behind Caddy.
- **Audit log (local):** auth events and destructive actions (erase, batch rollback) logged with timestamps.

---

## 6. Data integrity safeguards
- Money as `NUMERIC`/`Decimal` (no float drift).
- Idempotent, reversible imports (`import_batch` rollback).
- Foreign-key + check constraints (ownership sums to 100, unique dedup hash) enforced in DB, not just app.
- Scriptable backups + tested restore (NFR-REL-3).

---

## 7. Security checklist (pre-release)
- [ ] No component except `price_provider` opens an outbound socket (CI egress test passes).
- [ ] Postgres reachable only on internal network; no host port published.
- [ ] TLS active on all hops; HSTS + CSP headers present.
- [ ] Argon2id params benchmarked; login rate-limited.
- [ ] Secrets only via Docker secrets/.env; none in image layers (`docker history` clean).
- [ ] Backup encryption verified; restore rehearsed.
- [ ] GDPR export + erase verified to cover every table.
- [ ] Containers non-root; images audited.
