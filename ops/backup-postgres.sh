#!/usr/bin/env sh
set -eu

: "${POSTGRES_DB:?POSTGRES_DB required}"
: "${POSTGRES_USER:?POSTGRES_USER required}"
: "${POSTGRES_HOST:=db}"
: "${POSTGRES_PORT:=5432}"
: "${BACKUP_DIR:=/backups}"
: "${BACKUP_RETENTION_DAYS:=14}"

mkdir -p "$BACKUP_DIR"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
file="$BACKUP_DIR/${POSTGRES_DB}_${stamp}.dump"

pg_dump   --host "$POSTGRES_HOST"   --port "$POSTGRES_PORT"   --username "$POSTGRES_USER"   --format=custom   --compress=9   --file "$file"   "$POSTGRES_DB"

sha256sum "$file" > "$file.sha256"
find "$BACKUP_DIR" -type f \( -name '*.dump' -o -name '*.dump.sha256' \) -mtime "+$BACKUP_RETENTION_DAYS" -delete
printf 'backup=%s\n' "$file"
