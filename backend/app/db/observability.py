from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import func, select

from app.config import settings
from app.db.models.ai_call import AiCall
from app.db.models.pipeline_event import PipelineEvent
from app.db.sync_bridge import bridge_session
from app.utils.logger import get_logger

logger = get_logger()

_PRECOS_USD_1M = {
    'gemini-2.5-flash': {"input": 0.30, "output": 2.50},
}

def _rodar_async(coro_factory) -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro_factory())
        return

    import threading

    erro: dict = {}

    def _alvo():
        try:
            asyncio.run(coro_factory())
        except Exception as e:
            erro["e"] = e

    t = threading.Thread(target=_alvo, daemon=True)
    t.start()
    t.join(timeout=15)
    if "e" in erro:
        raise erro["e"]

def _estimar_custo(modelo: str, ti: int | None, to: int | None) -> float | None:
    p = _PRECOS_USD_1M.get(modelo)
    if not p or ti is None or to is None:
        return None
    return round((ti / 1_000_000) * p["input"] + (to / 1_000_000) * p["output"], 6)


# Registro de chamadas de IA
@dataclass
class AiCallRecord:
    agente: str = 'desconhecido'
    operacao: str | None = None
    provider: str = '?'
    modelo: str = '?'
    prompt: str | None = None
    resposta: str | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    latencia_ms: int | None = None
    sucesso: bool = True
    finish_reason: str | None = None
    erro: str | None = None
    empresa_cnpj: str | None = None


async def _registrar_ai_call_async(rec: AiCallRecord) -> None:
    guardar = settings.observ_store_payloads
    ti, to = rec.tokens_input, rec.tokens_output
    total = (ti or 0) + (to or 0) if (ti is not None or to is not None) else None

    async with bridge_session() as session:
        session.add(AiCall(
            agente=rec.agente,
            operacao=rec.operacao,
            provider=rec.provider,
            modelo=rec.modelo,
            prompt=rec.prompt if guardar else None,
            resposta=rec.resposta if guardar else None,
            prompt_chars=len(rec.prompt) if rec.prompt else None,
            resposta_chars=len(rec.resposta) if rec.resposta else None,
            tokens_input=ti,
            tokens_output=to,
            tokens_total=total,
            custo_usd=_estimar_custo(rec.modelo, ti, to),
            latencia_ms=rec.latencia_ms,
            finish_reason=rec.finish_reason,
            sucesso=rec.sucesso,
            error_message=rec.erro,
            empresa_cnpj=rec.empresa_cnpj,
        ))
        await session.commit()


def register_ai_call(rec: AiCallRecord) -> None:
    if not settings.observer_enabled:
        return
    try:
        _rodar_async(lambda: _registrar_ai_call_async(rec))
    except Exception as e:
        logger.warning(
            f"Observabilidade: Falha ao gravar ai_call: {type(e).__name__}: {e}"
        )

# Registro de evento de pipeline


async def _registrar_evento_async(
    evento: str, status: str, detalhe: str | None,
    empresa_cnpj: str | None, duracao_ms: int | None,
) -> None:
    async with bridge_session() as session:
        session.add(PipelineEvent(
            evento=evento, status=status, detalhe=detalhe,
            empresa_cnpj=empresa_cnpj, duracao_ms=duracao_ms,
        ))
        await session.commit()


def registrar_evento(
    evento: str,
    *,
    status: str = "ok",
    detalhe: str | None = None,
    empresa_cnpj: str | None = None,
    duracao_ms: int | None = None,
) -> None:
    if not settings.observer_enabled:
        return
    try:
        _rodar_async(
            lambda: _registrar_evento_async(
                evento, status, detalhe, empresa_cnpj, duracao_ms
            )
        )
    except Exception as e:
        logger.warning(
            f" Observabilidade: falha ao gravar evento '{evento}': "
            f"{type(e).__name__}: {e}"
        )

# stats pro endpoint


async def _stats_async() -> dict:
    async with bridge_session() as session:
        total = await session.scalar(select(func.count(AiCall.id))) or 0
        falhas = await session.scalar(
            select(func.count(AiCall.id)).where(AiCall.sucesso.is_(False))
        ) or 0
        tokens = await session.scalar(
            select(func.coalesce(func.sum(AiCall.tokens_total), 0))
        ) or 0
        custo = await session.scalar(
            select(func.coalesce(func.sum(AiCall.custo_usd), 0))
        ) or 0
        lat_media = await session.scalar(select(func.avg(AiCall.latencia_ms)))
        eventos = await session.scalar(select(func.count(PipelineEvent.id))) or 0

        return {
            "ai_calls_total": int(total),
            "ai_calls_falhas": int(falhas),
            "tokens_total": int(tokens),
            "custo_usd_estimado": float(custo),
            "latencia_media_ms": round(float(lat_media)) if lat_media else None,
            "pipeline_events_total": int(eventos),
        }


def stats_sync() -> dict:
    return asyncio.run(_stats_async())
