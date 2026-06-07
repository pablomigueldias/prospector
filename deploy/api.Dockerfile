# =============================================================================
# api.Dockerfile — imagem da API FastAPI (Prospector + financas)
# Build context = raiz do repo (ver docker-compose: context: ..)
#
# No start: roda 'alembic upgrade head' e sobe uvicorn em app.api.main:app.
# =============================================================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Sao_Paulo

WORKDIR /app

# Dependências de sistema (build de wheels + libs que o Playwright precisa)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instala as deps Python primeiro (cacheia melhor)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Navegador do Playwright (CPU — chromium) + libs de sistema dele
RUN playwright install --with-deps chromium

# Código da API
COPY backend/ ./

EXPOSE 8000

# Migrações + servidor. app.api.main:app é o ASGI app do FastAPI.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.api.main:app --host 0.0.0.0 --port 8000"]
