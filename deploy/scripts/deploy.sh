#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."
test -f .env || { echo "missing deploy/.env" >&2; exit 1; }

docker compose pull
# Migration is an explicit release gate. If it fails, this script stops before starting containers.
docker compose run --rm backend alembic upgrade head
docker compose up -d
docker compose ps
./scripts/healthcheck.sh
