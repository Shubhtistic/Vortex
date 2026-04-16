#!/bin/bash
set -e


echo "Checking if Postgres is ready at postgres_database:5432..."

# -h: host, -p: port, -U: user
until pg_isready -h postgres_database -p 5432 -U "${POSTGRES_USER}"; do
  echo "Postgres is starting up... waiting"
  sleep 2s
done


# now role based log
if [[ "$*" == *"uvicorn"* ]]; then
    echo "api detected running migrations"
    alembic upgrade head
else
    echo "worker detected"
    sleep 2s
fi


# hand control to cmd
# fastapi -> pid 1
exec "$@"