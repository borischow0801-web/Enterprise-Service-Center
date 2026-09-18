#!/usr/bin/env sh
set -eu

if [ "${1:-}" = "" ]; then
  echo "usage: $0 <image-tag-to-rollback-to>" >&2
  exit 1
fi

cd "$(dirname "$0")/.."
test -f .env || { echo "missing deploy/.env" >&2; exit 1; }

cp .env ".env.before-rollback.$(date +%Y%m%d%H%M%S)"
if grep -q '^IMAGE_TAG=' .env; then
  sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=$1/" .env
else
  printf '\nIMAGE_TAG=%s\n' "$1" >> .env
fi

echo "Rolled IMAGE_TAG back to $1. Database schema is not automatically downgraded."
docker compose pull
docker compose up -d
docker compose ps
./scripts/healthcheck.sh
