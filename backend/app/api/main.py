from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import admin_usuarios as admin_usuarios_router
from app.api.routers import agents as agents_router
from app.api.routers import auth as auth_router
from app.api.routers import cartoes as cartoes_router
from app.api.routers import categorias as categorias_router
from app.api.routers import compras as compras_router
from app.api.routers import comprovantes as comprovantes_router
from app.api.routers import contas as contas_router
from app.api.routers import copywriter as copywriter_router
from app.api.routers import crm as crm_router
from app.api.routers import dev_tools as dev_tools_router
from app.api.routers import eventos as eventos_router
from app.api.routers import freela as freela_router
from app.api.routers import importador as importador_router
from app.api.routers import leituras as leituras_router
from app.api.routers import memoria as memoria_router
from app.api.routers import nlu as nlu_router
from app.api.routers import observability as observability_router
from app.api.routers import orcamentos as orcamentos_router
from app.api.routers import orchestrator as orchestrator_router
from app.api.routers import outreach as outreach_router
from app.api.routers import pagar_mes as pagar_mes_router
from app.api.routers import perfil as perfil_router
from app.api.routers import pix as pix_router
from app.api.routers import prospector as prospector_router
from app.api.routers import recorrencias as recorrencias_router
from app.api.routers import resumo as resumo_router
from app.api.routers import telegram as telegram_router
from app.api.routers import transacoes as transacoes_router
from app.api.routers import vagas as vagas_router
from app.api.services.auth.cookie import cookie_name
from app.api.services.auth.csrf import valido as csrf_valido
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 API da Reativa subindo...")
    agendador = None
    if settings.scheduler_enabled:
        # Agendador in-process: 1x/dia processa recorrências e manda o lembrete
        # de vencimento no Telegram. (1 worker → sem risco de envio duplicado.)
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        from app.jobs.lembretes import rotina_diaria

        agendador = AsyncIOScheduler(timezone=settings.timezone)
        agendador.add_job(
            rotina_diaria,
            CronTrigger(hour=settings.lembretes_hora, minute=0),
            id="rotina_diaria",
            replace_existing=True,
        )
        if settings.briefing_enabled:
            from app.jobs.briefing import rotina_briefing
            agendador.add_job(
                rotina_briefing,
                CronTrigger(hour=settings.briefing_hora, minute=0),
                id="rotina_briefing",
                replace_existing=True,
            )
        agendador.start()
        logger.info(
            "⏰ Agendador ligado (rotina %sh · briefing %sh).",
            settings.lembretes_hora, settings.briefing_hora,
        )
    yield
    if agendador is not None:
        agendador.shutdown(wait=False)
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
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_METODOS_MUTACAO = {"POST", "PUT", "PATCH", "DELETE"}

# Rotas isentas de CSRF mesmo com cookie de sessão presente. O login
# estabelece uma sessão nova (rotaciona sessão + token CSRF), então não faz
# sentido — e quebra o onboarding — exigir CSRF aqui: um cookie de sessão
# velho/expirado no navegador trava a re-autenticação.
_CSRF_ISENTAS = {"/api/auth/login"}


@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    """Exige CSRF só quando a mutação vem autenticada por cookie de sessão.

    Requests sem cookie de sessão (webhook do Telegram com secret, clientes de
    API) e as rotas de ``_CSRF_ISENTAS`` (login) passam direto.
    """
    if (
        request.method in _METODOS_MUTACAO
        and request.url.path not in _CSRF_ISENTAS
        and request.cookies.get(cookie_name())
    ):
        if not csrf_valido(request):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token inválido ou ausente."},
            )
    return await call_next(request)


@app.get("/api/health", tags=["meta"])
def healthcheck() -> dict:
    return {"status": "ok", "service": "reativa-agents-api"}


# ── Autenticação (portão de entrada) ──────────────────────────────
app.include_router(auth_router.router)
app.include_router(admin_usuarios_router.router)

app.include_router(agents_router.router)
app.include_router(prospector_router.router)
app.include_router(copywriter_router.router)
app.include_router(crm_router.router)
app.include_router(memoria_router.router)
app.include_router(orchestrator_router.router)
app.include_router(observability_router.router)
app.include_router(outreach_router.router)

# ── Área pessoal (separada da Reative) ────────────────────────────
app.include_router(perfil_router.router)
app.include_router(vagas_router.router)
app.include_router(freela_router.router)

# ── Organizador Financeiro (domínio pessoal) ──────────────────────
app.include_router(contas_router.router)
app.include_router(categorias_router.router)
app.include_router(transacoes_router.router)
app.include_router(resumo_router.router)
app.include_router(cartoes_router.router)
app.include_router(compras_router.router)
app.include_router(recorrencias_router.router)
app.include_router(orcamentos_router.router)
app.include_router(pagar_mes_router.router)
app.include_router(leituras_router.router)
app.include_router(comprovantes_router.router)
app.include_router(importador_router.router)
app.include_router(nlu_router.router)
app.include_router(pix_router.router)
app.include_router(telegram_router.router)
app.include_router(eventos_router.router)

# ── Ferramentas de dev (rotas guardadas por DEV_TOOLS_ENABLED) ────
app.include_router(dev_tools_router.router)
