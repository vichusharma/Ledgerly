#!/usr/bin/env bash
# Backup Ledgerly Postgres data to a timestamped .sql.gz file.
# Usage: ./scripts/backup.sh [output_dir]
set -euo pipefail

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/ledgerly_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "▶ Backing up database to $FILE …"
docker compose exec -T db \
    pg_dump -U "${POSTGRES_USER:-ledgerly}" "${POSTGRES_DB:-ledgerly}" \
  | gzip > "$FILE"

echo "✔ Backup complete: $FILE ($(du -h "$FILE" | cut -f1))"
