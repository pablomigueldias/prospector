#!/usr/bin/env bash
# =============================================================================
# set-telegram-webhook.sh — registra o webhook do bot no Telegram
#
# Rode SÓ depois que o HTTPS estiver no ar (cadeado verde) e a API respondendo.
#   ./scripts/set-telegram-webhook.sh
#
# Usa DOMAIN, TELEGRAM_BOT_TOKEN e TELEGRAM_WEBHOOK_SECRET do .env.
# O endpoint final é:  https://$DOMAIN/telegram/webhook
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

# Lê só as chaves necessárias do .env (sem 'source' — valores podem ter espaços).
envget() { grep -E "^$1=" .env | head -1 | cut -d= -f2-; }
TELEGRAM_BOT_TOKEN="$(envget TELEGRAM_BOT_TOKEN)"
DOMAIN="$(envget DOMAIN)"
TELEGRAM_WEBHOOK_SECRET="$(envget TELEGRAM_WEBHOOK_SECRET)"

: "${TELEGRAM_BOT_TOKEN:?defina TELEGRAM_BOT_TOKEN no .env}"
: "${DOMAIN:?defina DOMAIN no .env}"
: "${TELEGRAM_WEBHOOK_SECRET:?defina TELEGRAM_WEBHOOK_SECRET no .env}"

WEBHOOK_URL="https://${DOMAIN}/telegram/webhook"

echo ">> Registrando webhook: ${WEBHOOK_URL}"
curl -fsS -X POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=${WEBHOOK_URL}" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}" \
  -d "drop_pending_updates=true"
echo ""

echo ">> Status atual do webhook:"
curl -fsS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
echo ""
