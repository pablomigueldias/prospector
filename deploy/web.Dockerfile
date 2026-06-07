# =============================================================================
# web.Dockerfile — front Next.js (build standalone)
# Build context = raiz do repo (ver docker-compose: context: ..)
#
# PRÉ-REQUISITO (RUNBOOK Etapa 7.1): next.config.js precisa ter
#   const nextConfig = { reactStrictMode: true, output: 'standalone' };
# Sem 'output: standalone' o estágio runner não encontra o server.js.
# =============================================================================

# --- deps: instala node_modules a partir do lockfile -------------------------
FROM node:20-alpine AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# --- builder: compila o Next -------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
# URL da API embutida no bundle (variável NEXT_PUBLIC_*)
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# --- runner: imagem final enxuta --------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Usuário sem privilégio
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

# Saída standalone do Next (inclui server.js + node_modules mínimos)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
# Se você criar frontend/public/ depois, descomente:
# COPY --from=builder /app/public ./public

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
