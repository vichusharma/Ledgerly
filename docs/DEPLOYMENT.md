# Ledgerly — Deployment

Related: [ARCHITECTURE](./ARCHITECTURE.md) · [SECURITY](./SECURITY.md)

Goal: **`docker compose up` brings the entire stack up on one node.** Single-command local deploy; optional future cloud extension without re-architecting.

---

## 1. Topology (single-node)

```
                        host:443 (HTTPS)
                              │
                       ┌──────▼──────┐
                       │    caddy    │  TLS termination + reverse proxy + headers
                       └──┬───────┬──┘
                /         │       │  /api
                ▼         │       ▼
          ┌──────────┐    │   ┌──────────┐      ┌──────────┐
          │   web    │    │   │   api    │─────►│  redis   │ (optional)
          │ Next.js  │    │   │ FastAPI  │      └──────────┘
          └──────────┘    │   └────┬─────┘
                          │        ▼
                          │   ┌──────────┐
                          │   │ postgres │  (encrypted volume, not host-exposed)
                          │   └──────────┘
                          └── internal docker network only
```

Only Caddy publishes a host port (443, and 80→redirect). Postgres/Redis have **no published ports**.

---

## 2. docker-compose.yml (shape)

```yaml
services:
  caddy:
    image: caddy:2
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
    depends_on: [web, api]

  web:
    build: ./web
    environment:
      - NEXT_PUBLIC_API_BASE=https://localhost/api
    expose: ["3000"]
    depends_on: [api]

  api:
    build: ./api
    environment:
      - DATABASE_URL=postgresql+psycopg://ledgerly:@postgres:5432/ledgerly
      - REDIS_URL=redis://redis:6379/0
    secrets: [postgres_password, app_secret_key, pgcrypto_key]
    expose: ["8000"]
    depends_on:
      postgres: { condition: service_healthy }

  postgres:
    image: postgres:16
    environment:
      - POSTGRES_USER=ledgerly
      - POSTGRES_DB=ledgerly
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
    secrets: [postgres_password]
    volumes: ["pgdata:/var/lib/postgresql/data"]   # place on an encrypted disk
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ledgerly"]
      interval: 5s
      retries: 10
    # NOTE: no `ports:` — internal network only

  redis:                       # optional in MVP
    image: redis:7
    expose: ["6379"]

volumes:
  pgdata:
  caddy_data:

secrets:
  postgres_password: { file: ./secrets/postgres_password }
  app_secret_key:    { file: ./secrets/app_secret_key }
  pgcrypto_key:      { file: ./secrets/pgcrypto_key }
```

### Caddyfile (shape)
```
localhost {
  encode gzip
  header {
    Strict-Transport-Security "max-age=31536000"
    X-Content-Type-Options nosniff
    X-Frame-Options DENY
    Referrer-Policy no-referrer
  }
  handle /api/* {
    reverse_proxy api:8000
  }
  handle {
    reverse_proxy web:3000
  }
}
```
Caddy's internal CA issues the local cert automatically; for a fully-trusted cert use `mkcert` and mount it.

---

## 3. First-run / bootstrap
```bash
git clone … && cd ledgerly
cp .env.example .env                 # edit values
./scripts/gen_secrets.sh             # creates ./secrets/* (random)
docker compose up -d --build
docker compose exec api alembic upgrade head   # migrations
docker compose exec api python -m app.scripts.create_user   # set household password + recovery codes
# open https://localhost
```
Optional demo data: `docker compose exec api python -m app.scripts.seed`.

---

## 4. Backup & restore (NFR-REL-3)
```bash
# scripts/backup.sh  — encrypted dump
docker compose exec -T postgres pg_dump -U ledgerly ledgerly \
  | age -p > backups/ledgerly_$(date +%F).sql.age

# scripts/restore.sh
age -d backups/<file>.sql.age \
  | docker compose exec -T postgres psql -U ledgerly ledgerly
```
Schedule via host cron or the in-app APScheduler. Keep `caddy_data` and `secrets/` backed up separately and securely.

---

## 5. Operations
- **Logs:** `docker compose logs -f api web` — structured JSON; no external telemetry.
- **Health:** `GET https://localhost/api/health`; compose healthchecks gate startup ordering.
- **Upgrades:** `git pull && docker compose up -d --build && alembic upgrade head`. Migrations forward-only.
- **Resource footprint:** comfortably runs in ~1–2 GB RAM; suitable for a laptop or a home NAS (Synology/Unraid support compose).

---

## 6. Optional future cloud extension (not MVP)
The same compose stack lifts to a **single small VM** (Hetzner/OVH/Scaleway — EU for data residency) behind Caddy with a real domain + Let's Encrypt (Caddy automates ACME). Nothing in the architecture assumes localhost: switch the Caddy site address from `localhost` to the domain and point DNS. Multi-user SaaS would require real tenancy and is explicitly out of scope (see [PRD non-goals](./PRD.md)). For personal remote access, prefer a **Tailscale/WireGuard** tunnel over exposing the VM publicly — keeps the privacy posture intact.
