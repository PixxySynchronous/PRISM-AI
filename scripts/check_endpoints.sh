#!/usr/bin/env bash
# Simple script to sanity-check service endpoints (status + roster)
set -euo pipefail
BASE=${1:-http://localhost:8080}

echo "Checking status at $BASE/api/attendance/status"
curl -sS -f "$BASE/api/attendance/status" | jq .

echo "\nChecking roster at $BASE/api/attendance/roster"
curl -sS -f "$BASE/api/attendance/roster" | jq .
