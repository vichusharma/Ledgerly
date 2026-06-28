#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Ledgerly — full-stack verification script
#
# Runs in order:
#   1. Unit tests (pure Python, no DB needed)
#   2. Integration tests (spins up ephemeral Postgres via docker-compose.test.yml)
#   3. docker compose build (validates both Dockerfiles)
#   4. Health check against the full stack
#   5. Backup + restore smoke test
#
# Usage:
#   bash scripts/verify.sh          # all checks
#   bash scripts/verify.sh unit     # unit tests only
#   bash scripts/verify.sh int      # integration tests only
#   bash scripts/verify.sh build    # docker build only
#   bash scripts/verify.sh health   # stack health only
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

STEP="${1:-all}"
PASS=0
FAIL=0

green() { echo -e "\033[32m✓ $*\033[0m"; }
red()   { echo -e "\033[31m✗ $*\033[0m"; }
bold()  { echo -e "\033[1m==> $*\033[0m"; }

check() {
  local label="$1"; shift
  if "$@" > /tmp/ledgerly_check.log 2>&1; then
    green "$label"
    ((PASS++)) || true
  else
    red "$label"
    cat /tmp/ledgerly_check.log
    ((FAIL++)) || true
  fi
}

# ── 1. Unit tests ─────────────────────────────────────────────────────────────
run_unit() {
  bold "Unit tests (core/ math)"
  check "amortization golden tests" \
    docker compose -f docker-compose.test.yml run --rm --no-deps api-test \
      sh -c "pip install -e '.[dev]' -q && pytest app/tests/unit/ -v --tb=short"
}

# ── 2. Integration tests ──────────────────────────────────────────────────────
run_integration() {
  bold "Integration tests (auth, accounts, transactions, net worth)"
  check "integration test suite" \
    docker compose -f docker-compose.test.yml run --rm api-test
  docker compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
}

# ── 3. Docker build ───────────────────────────────────────────────────────────
run_build() {
  bold "Docker build (api + web)"
  check "api image build"  docker compose build api
  check "web image build"  docker compose build web
}

# ── 4. Health check ───────────────────────────────────────────────────────────
run_health() {
  bold "Stack health check"

  docker compose up -d db api
  echo "  Waiting for API to be ready…"
  for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  check "GET /health returns 200" \
    bash -c 'curl -sf http://localhost:8000/health | grep -q "ok"'

  check "GET /api/v1/auth/session returns 401 (no cookie)" \
    bash -c 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/auth/session | grep -q 401'

  docker compose stop api db 2>/dev/null || true
}

# ── 5. Backup/restore smoke test ──────────────────────────────────────────────
run_backup() {
  bold "Backup/restore smoke test"
  mkdir -p backups
  check "backup script runs" bash scripts/backup.sh
  LATEST=$(ls -t backups/*.sql.gz 2>/dev/null | head -1)
  if [[ -n "$LATEST" ]]; then
    green "Backup file created: $LATEST ($(du -sh "$LATEST" | cut -f1))"
  else
    red "No backup file found"
    ((FAIL++)) || true
  fi
}

# ── Run selected steps ─────────────────────────────────────────────────────────
case "$STEP" in
  unit)        run_unit ;;
  int)         run_integration ;;
  build)       run_build ;;
  health)      run_health ;;
  backup)      run_backup ;;
  all)
    run_unit
    run_integration
    run_build
    run_health
    run_backup
    ;;
  *)
    echo "Unknown step: $STEP"
    echo "Usage: $0 [unit|int|build|health|backup|all]"
    exit 1
    ;;
esac

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
bold "Results: ${PASS} passed, ${FAIL} failed"
[[ $FAIL -eq 0 ]] && green "All checks passed — ready to ship." || red "Some checks failed."
exit $FAIL
