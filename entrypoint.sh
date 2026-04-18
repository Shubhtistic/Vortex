#!/bin/bash
set -e

echo "Checking if Postgres is ready at ${POSTGRES_SERVER}:5432..."

# -h: host, -p: port, -U: user
until pg_isready -h "${POSTGRES_SERVER}" -p 5432 -U "${POSTGRES_USER}"; do
  echo "Postgres is starting up... waiting"
  sleep 2s
done

echo "Postgres is ready!"

# hand control to cmd
# fastapi/celery -> pid 1
exec "$@"