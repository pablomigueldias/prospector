#!/usr/bin/env bash
# =============================================================================
# backup.sh — dump do Postgres com rotação de 14 dias
#
# Manual:   ./scripts/backup.sh
# Cron (3h da manhã):
#   0 3 * * * /home/deploy/reative/deploy/scripts/backup.sh >> /home/deploy/backup.log 2>&1
#
# Restore (teste antes de confiar!):
#   gunzip -c ~/backups/ARQUIVO.sql.gz | \
#     docker compose -f ~/reative/deploy/docker-compose.yml exec -T db \
#     psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

# Lê só as chaves necessárias do .env (sem 'source' — valores podem ter espaços,
# o que quebraria o parser do shell, ex.: MAIL_FROM_NAME=Reative Systems).
envget() { grep -E "^$1=" .env | head -1 | cut -d= -f2-; }
POSTGRES_USER="$(envget POSTGRES_USER)"
POSTGRES_DB="$(envget POSTGRES_DB)"
: "${POSTGRES_USER:?POSTGRES_USER não encontrado no .env}"
: "${POSTGRES_DB:?POSTGRES_DB não encontrado no .env}"

BACKUP_DIR="${HOME}/backups"
RETENTION_DAYS=14
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${BACKUP_DIR}/${POSTGRES_DB}-${STAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo ">> [$(date '+%F %T')] Dump de '${POSTGRES_DB}'..."
docker compose exec -T db \
  pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
  | gzip > "$OUT"

SIZE="$(du -h "$OUT" | cut -f1)"
echo ">> OK: ${OUT} (${SIZE})"

echo ">> Rotação: removendo dumps com mais de ${RETENTION_DAYS} dias..."
find "$BACKUP_DIR" -name "${POSTGRES_DB}-*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

echo ">> Backups atuais:"
ls -1t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | head
