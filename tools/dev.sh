#!/usr/bin/env bash
# Local dev helper (Linux, PostgreSQL 16 installed). Starts Postgres if needed, creates the dev DB, runs the server on :3100.
# In dev (no BREVO_API_KEY) the admin login code is printed to the server log. NEVER run production like this.
set -e
pg_lsclusters 2>/dev/null | grep -q online || { pg_ctlcluster 16 main start; sleep 3; }
su postgres -c "psql -tAc \"select 1 from pg_roles where rolname='app'\"" | grep -q 1 || su postgres -c "psql -qc \"create role app login password 'apppw'\""
su postgres -c "psql -tAc \"select 1 from pg_database where datname='portfolio'\"" | grep -q 1 || su postgres -c "psql -qc 'create database portfolio owner app'"
cd "$(dirname "$0")/../server"
DATABASE_URL=${DATABASE_URL:-postgres://app:apppw@127.0.0.1:5432/portfolio} PORT=${PORT:-3100} setsid nohup node index.js > /tmp/server.log 2>&1 < /dev/null &
sleep 3; curl -s -m 3 "localhost:${PORT:-3100}/api/health" && echo " server up"
