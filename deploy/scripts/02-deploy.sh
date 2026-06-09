#!/usr/bin/env bash
# =============================================================================
# 02-deploy.sh — sobe / atualiza a stack
#
#   ./scripts/02-deploy.sh          → atualiza tudo (puxa git, builda api+web)
#   ./scripts/02-deploy.sh infra    → sobe SÓ a base (db + minio + caddy)
#
# Roda como usuário 'deploy', de dentro de ~/reative/deploy.
# =============================================================================
set -euo pipefail

# raiz do pacote deploy/ (independente de onde foi chamado)
cd "$(dirname "$0")/.."

MODE="${1:-full}"

if [ ! -f .env ]; then
  echo "ERRO: .env não encontrado. Rode: cp .env.example .env && nano .env"
  exit 1
fi

echo ">> Puxando últimas mudanças do git..."
git -C .. pull --ff-only || echo "   (git pull pulado — repo local ou sem upstream)"

if [ "$MODE" = "infra" ]; then
  echo ">> Subindo SÓ a infra (db + minio + caddy)..."
  docker compose up -d db minio caddy
else
  echo ">> Subindo a stack completa (build de api + web)..."
  docker compose up -d --build
fi

echo ""
echo ">> Limpando imagens órfãs..."
docker image prune -f >/dev/null 2>&1 || true

echo ""
docker compose ps
