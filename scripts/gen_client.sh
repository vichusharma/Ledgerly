#!/usr/bin/env bash
# Generate the typed TypeScript client from the FastAPI OpenAPI spec.
# Requires: npx openapi-typescript-codegen (or @hey-api/openapi-ts)
# Usage: ./scripts/gen_client.sh
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
OUT_DIR="./web/src/lib/api/generated"

echo "▶ Fetching OpenAPI spec from $API_URL/openapi.json …"
curl -sf "$API_URL/openapi.json" -o /tmp/ledgerly_openapi.json

echo "▶ Generating TypeScript client into $OUT_DIR …"
npx --yes @hey-api/openapi-ts \
    --input /tmp/ledgerly_openapi.json \
    --output "$OUT_DIR" \
    --client axios

echo "✔ Client generated: $OUT_DIR"
