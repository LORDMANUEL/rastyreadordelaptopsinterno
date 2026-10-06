#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: restore-postgres.sh /backups/file.dump" >&2
  exit 2
fi

file="$1"
: "${POSTGRES_DB:?POSTGRES_DB required}"
: "${POSTGRES_USER:?POSTGRES_USER required}"
: "${POSTGRES_HOST:=db}"
: "${POSTGRES_PORT:=5432}"

[ -f "$file" ] || { echo "backup not found: $file" >&2; exit 3; }
[ -f "$file.sha256" ] || { echo "checksum not found: $file.sha256" >&2; exit 4; }

(
  cd "$(dirname "$file")"
  sha256sum -c "$(basename "$file").sha256"
)

pg_restore   --host "$POSTGRES_HOST"   --port "$POSTGRES_PORT"   --username "$POSTGRES_USER"   --dbname "$POSTGRES_DB"   --clean   --if-exists   --no-owner   "$file"
