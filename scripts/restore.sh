#!/usr/bin/env bash
# Restore a Ledgerly backup.
# Usage: ./scripts/restore.sh <backup_file.sql.gz>
set -euo pipefail

BACKUP_FILE="${1:?Usage: restore.sh <backup_file.sql.gz>}"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Error: file not found: $BACKUP_FILE" >&2
    exit 1
fi

echo "⚠ This will DROP and recreate the ledgerly database. Continue? [y/N]"
read -r confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

echo "▶ Restoring from $BACKUP_FILE …"
gunzip -c "$BACKUP_FILE" | docker compose exec -T db \
    psql -U "${POSTGRES_USER:-ledgerly}" "${POSTGRES_DB:-ledgerly}"

echo "✔ Restore complete."
