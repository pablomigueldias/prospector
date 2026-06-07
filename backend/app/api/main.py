from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import agents as agents_router
from app.api.routers import prospector as prospector_router
from app.api.routers import copywriter as copywriter_router
from app.api.routers import observability as observability_router
from app.api.routers import outreach as outreach_router
from app.api.routers import perfil as perfil_router
from app.api.routers import vagas as vagas_router
from app.api.routers import contas as contas_router
from app.api.routers import categorias as categorias_router
from app.api.routers import transacoes as transacoes_router
from app.api.routers import resumo as resumo_router
from app.api.routers import cartoes as cartoes_router
from app.api.routers import compras as compras_router
from app.utils.logger import get_logger


logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 API da Reativa subindo...")
    yield
    logger.info("👋 API encerrando.")


app = FastAPI(
    title="Reative Systems — Plataforma de Agentes",
    description=(
        "API HTTP que orquestra os agentes da Reativa. Hoje: Prospector. "
        "No roadmap: Cobrança, Suporte, Onboarding."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["meta"])
def healthcheck() -> dict:
    return {"status": "ok", "service": "reativa-agents-api"}


app.include_router(agents_router.router)
app.include_router(prospector_router.router)
app.include_router(copywriter_router.router)
app.include_router(observability_router.router)
app.include_router(outreach_router.router)

# ── Área pessoal (separada da Reative) ────────────────────────────
app.include_router(perfil_router.router)
app.include_router(vagas_router.router)

# ── Organizador Financeiro (domínio pessoal) ──────────────────────
app.include_router(contas_router.router)
app.include_router(categorias_router.router)
app.include_router(transacoes_router.router)
app.include_router(resumo_router.router)
app.include_router(cartoes_router.router)
app.include_router(compras_router.router)