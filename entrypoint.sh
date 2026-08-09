#!/usr/bin/env bash
#
# Container entrypoint. Waits for the database, runs migrations, then
# executes whatever command was passed (default: the Django dev server).
#
# Environment variables used (all come from .env / docker-compose):
#   DB_HOST, DB_PORT, DB_ENGINE
#   DJANGO_MIGRATE_ON_START (default: true)
#   DJANGO_COLLECTSTATIC_ON_START (default: true)
#   DJANGO_LOADDATA_ON_START (optional: comma-separated fixture labels)

set -euo pipefail

# ---- 1. Wait for the database -------------------------------------------------
# Only relevant when running with the Postgres service. We poll the TCP port
# instead of relying on a heavier healthcheck script.
if [[ "${DB_ENGINE:-sqlite}" == "postgres" ]]; then
  echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST:-db}:${DB_PORT:-5432}..."
  for attempt in $(seq 1 60); do
    if (echo > "/dev/tcp/${DB_HOST:-db}/${DB_PORT:-5432}") >/dev/null 2>&1; then
      echo "[entrypoint] Database is reachable."
      break
    fi
    sleep 1
  done
  if ! (echo > "/dev/tcp/${DB_HOST:-db}/${DB_PORT:-5432}") >/dev/null 2>&1; then
    echo "[entrypoint] Database not reachable after 60s. Aborting." >&2
    exit 1
  fi
fi

# ---- 2. Migrations ------------------------------------------------------------
if [[ "${DJANGO_MIGRATE_ON_START:-true}" == "true" ]]; then
  echo "[entrypoint] Applying database migrations..."
  python manage.py migrate --noinput
fi

# ---- 3. Static files ----------------------------------------------------------
if [[ "${DJANGO_COLLECTSTATIC_ON_START:-true}" == "true" \
   && "${DJANGO_DEBUG:-True}" != "True" ]]; then
  echo "[entrypoint] Collecting static files..."
  python manage.py collectstatic --noinput
fi

# ---- 4. Optional fixtures -----------------------------------------------------
if [[ -n "${DJANGO_LOADDATA_ON_START:-}" ]]; then
  echo "[entrypoint] Loading fixtures: ${DJANGO_LOADDATA_ON_START}"
  IFS=',' read -ra FIXTURES <<< "${DJANGO_LOADDATA_ON_START}"
  for fixture in "${FIXTURES[@]}"; do
    python manage.py loaddata "${fixture}"
  done
fi

# ---- 5. Hand off to CMD -------------------------------------------------------
echo "[entrypoint] Starting: $*"
exec "$@"
