#!/bin/bash
set -e

echo "ChainFinity API starting..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until nc -z "${DB_HOST:-postgres}" "${DB_PORT:-5432}"; do
    echo "PostgreSQL not ready, waiting..."
    sleep 2
done
echo "PostgreSQL is ready."

# Wait for Redis
echo "Waiting for Redis..."
until nc -z "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}"; do
    echo "Redis not ready, waiting..."
    sleep 2
done
echo "Redis is ready."

# Run Alembic migrations
echo "Running database migrations..."
cd /app && alembic upgrade head
echo "Migrations complete."

exec "$@"
