#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."
test -f .env || { echo "missing deploy/.env" >&2; exit 1; }

echo "Before updating: back up MySQL and uploads. Continue only after backup is complete."
docker compose pull
docker compose run --rm backend alembic upgrade head
docker compose up -d
docker compose ps
./scripts/healthcheck.sh
