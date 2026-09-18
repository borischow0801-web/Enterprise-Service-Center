#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://127.0.0.1}"

echo "[health] API: ${BASE_URL}/api/health"
curl -fsS "${BASE_URL}/api/health" >/dev/null

echo "[health] H5: ${BASE_URL}/"
curl -fsS "${BASE_URL}/" >/dev/null

echo "[health] Admin: ${BASE_URL}/admin/"
curl -fsS "${BASE_URL}/admin/" >/dev/null

echo "[health] OK"
