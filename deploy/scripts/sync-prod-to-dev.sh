#!/usr/bin/env bash
# =============================================================================
# sync-prod-to-dev.sh — copia os DADOS de PRODUÇÃO para o banco de DEV (local).
#
#   ONE-WAY por design: este script SÓ LÊ a produção (pg_dump) e SÓ ESCREVE no
#   container de banco LOCAL (dev). Não existe — de propósito — caminho de
#   dev → produção. O deploy (rsync) também nunca toca no volume do banco do
#   VPS, então dado de dev jamais sobe pra produção.
#
#   Use pra ter dados reais no dev e testar à vontade:
#       ./deploy/scripts/sync-prod-to-dev.sh
#
#   ATENÇÃO: isto SUBSTITUI o banco de dev inteiro pelo de produção
#   (DROP + CREATE). Tudo que você tinha só no dev é perdido. A senha de login
#   do dev passa a ser a MESMA da produção (vem junto no schema auth).
#
#   Rode da sua máquina de dev (precisa de: ssh pro VPS + container local no ar).
# =============================================================================
set -euo pipefail

VPS="${VPS:-deploy@178.105.157.102}"
PROD_CONTAINER="reative-db"     # nome do container no VPS
DEV_CONTAINER="${DEV_CONTAINER:-reative-db}"  # container local (dev), porta 5433
DEV_DB="${DEV_DB:-reative}"
DEV_USER="${DEV_USER:-reative}"

red()  { printf '\033[31m%s\033[0m\n' "$*"; }
bold() { printf '\033[1m%s\033[0m\n'  "$*"; }

bold ">> sync produção → dev"
echo "   origem : $VPS  (container $PROD_CONTAINER)  [somente leitura]"
echo "   destino: container local $DEV_CONTAINER, banco '$DEV_DB'"
red  "   Isto APAGA o banco de dev e o substitui pela produção."
read -r -p "   Continuar? [s/N] " ok
[ "${ok:-}" = "s" ] || [ "${ok:-}" = "S" ] || { echo "   abortado."; exit 1; }

# 1) Dump da produção (pg_dump roda DENTRO do container do VPS; só leitura).
DUMP="$(mktemp -t prod_dump.XXXXXX.sql)"
trap 'rm -f "$DUMP"' EXIT
bold ">> Dump da produção..."
ssh "$VPS" "docker exec $PROD_CONTAINER sh -c 'pg_dump -U \$POSTGRES_USER -d \$POSTGRES_DB --no-owner --no-privileges'" > "$DUMP"
echo "   dump: $(du -h "$DUMP" | cut -f1)"
[ -s "$DUMP" ] || { red "   dump vazio — abortando (nada foi alterado no dev)."; exit 1; }

# 2) Recria o banco de dev (derruba conexões e dropa com FORCE — PG13+).
bold ">> Recriando o banco de dev (DROP + CREATE)..."
docker exec "$DEV_CONTAINER" psql -U "$DEV_USER" -d postgres -q \
  -c "DROP DATABASE IF EXISTS $DEV_DB WITH (FORCE);" \
  -c "CREATE DATABASE $DEV_DB;"

# 3) Restaura o dump no banco de dev.
bold ">> Restaurando na dev..."
docker exec -i "$DEV_CONTAINER" psql -U "$DEV_USER" -d "$DEV_DB" -q -v ON_ERROR_STOP=1 < "$DUMP" >/dev/null

bold ">> Pronto — o dev agora espelha a produção."
echo "   Reinicie a API de dev (ela pode ter perdido a conexão durante o DROP)."
echo "   Login do dev = mesmas credenciais da produção."
