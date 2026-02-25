#!/bin/bash
set -e

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until nc -z $POSTGRES_DNS 5432; do
  sleep 2
done

echo "Initializing schema if needed..."
${HIVE_HOME}/bin/schematool -dbType postgres -initSchema || true

echo "Starting Hive Metastore..."
exec ${HIVE_HOME}/bin/hive --service metastore