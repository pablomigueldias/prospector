"""Memória compartilhada do MAS (blackboard) — MAS-1.

Toda ação relevante de um agente (ou edição manual) vira um `AgenteEvento`
amarrado a um alvo (vaga/empresa/negocio/contato/projeto/atividade/freela…).
Qualquer agente lê a linha do tempo do alvo pra saber o que já foi feito — é o
substrato que destrava a coordenação (ver docs/plano-agentes-autonomos.md).

`registrar` é best-effort: nunca derruba o fluxo de quem chamou (a memória é
acessória; se falhar, loga e segue).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select

from app.api.schemas.memoria import EventoCreate, EventoOut, TimelineResponse
from app.db.models.agente_evento import AgenteEvento
from app.db.session import get_session
from app.utils.logger import get_logger

logger = get_logger()


def _to_out(e: AgenteEvento) -> EventoOut:
    return EventoOut(
        id=str(e.id),
        agente=e.agente,
        alvo_tipo=e.alvo_tipo,
        alvo_id=e.alvo_id,
        tipo=e.tipo,
        resumo=e.resumo,
        payload=e.payload,
        origem=e.origem,
        created_at=e.created_at.isoformat() if e.created_at else "",
    )


async def registrar(
    *,
    agente: str,
    alvo_tipo: str,
    alvo_id: str,
    tipo: str,
    resumo: str | None = None,
    payload: dict[str, Any] | None = None,
    origem: str = "manual",
) -> None:
    """Grava um evento na memória. Best-effort: erros não propagam."""
    if not alvo_tipo or not alvo_id:
        return
    try:
        async with get_session() as session:
            session.add(AgenteEvento(
                agente=agente, alvo_tipo=alvo_tipo, alvo_id=str(alvo_id),
                tipo=tipo, resumo=resumo, payload=payload, origem=origem,
            ))
            await session.commit()
    except Exception as e:  # noqa: BLE001 — memória é acessória
        logger.warning("memoria_service.registrar falhou: {}", e)


async def criar(p: EventoCreate) -> EventoOut:
    """Cria um evento explicitamente (ex: nota manual na timeline)."""
    async with get_session() as session:
        ev = AgenteEvento(
            agente=p.agente, alvo_tipo=p.alvo_tipo, alvo_id=str(p.alvo_id),
            tipo=p.tipo, resumo=p.resumo, payload=p.payload, origem=p.origem,
        )
        session.add(ev)
        await session.commit()
        await session.refresh(ev)
        return _to_out(ev)


# ── Outcomes (MAS-3): loop de aprendizado ────────────────────────────
# Resultado de um alvo, com sinal: +1 deu retorno, -1 não, 0 neutro.
_OUTCOME_SINAL: dict[str, int] = {
    "respondido": 1, "reuniao": 1, "entrevista": 1, "oferta": 1,
    "ganho": 1, "fechou": 1,
    "sem_resposta": -1, "recusado": -1, "perdido": -1, "desisti": -1,
}


def outcomes_vocabulario() -> dict[str, int]:
    return dict(_OUTCOME_SINAL)


async def registrar_outcome(
    alvo_tipo: str, alvo_id: str, resultado: str, nota: str | None = None,
) -> None:
    sinal = _OUTCOME_SINAL.get(resultado, 0)
    await registrar(
        agente="usuario", alvo_tipo=alvo_tipo, alvo_id=alvo_id, tipo="outcome",
        resumo=f"Resultado: {resultado}" + (f" — {nota}" if nota else ""),
        payload={"resultado": resultado, "sinal": sinal}, origem="manual",
    )


async def resumo_outcomes() -> dict[str, Any]:
    """Agrega os outcomes do blackboard → 'o que tem dado retorno'."""
    async with get_session() as session:
        rows = (await session.execute(
            select(AgenteEvento).where(AgenteEvento.tipo == "outcome")
        )).scalars().all()
    por_resultado: dict[str, int] = {}
    por_alvo_tipo: dict[str, dict[str, int]] = {}
    positivos = negativos = 0
    for r in rows:
        res = (r.payload or {}).get("resultado", "?")
        sinal = (r.payload or {}).get("sinal", 0)
        por_resultado[res] = por_resultado.get(res, 0) + 1
        bucket = por_alvo_tipo.setdefault(
            r.alvo_tipo, {"positivos": 0, "negativos": 0, "total": 0})
        bucket["total"] += 1
        if sinal > 0:
            positivos += 1
            bucket["positivos"] += 1
        elif sinal < 0:
            negativos += 1
            bucket["negativos"] += 1
    base = positivos + negativos
    return {
        "total": len(rows),
        "positivos": positivos,
        "negativos": negativos,
        "taxa_positiva": round(positivos / base, 3) if base else None,
        "por_resultado": por_resultado,
        "por_alvo_tipo": por_alvo_tipo,
    }


async def timeline(
    alvo_tipo: str, alvo_id: str, limite: int = 200
) -> TimelineResponse:
    async with get_session() as session:
        rows = (await session.execute(
            select(AgenteEvento)
            .where(
                AgenteEvento.alvo_tipo == alvo_tipo,
                AgenteEvento.alvo_id == str(alvo_id),
            )
            .order_by(desc(AgenteEvento.created_at))
            .limit(limite)
        )).scalars().all()
    return TimelineResponse(
        alvo_tipo=alvo_tipo, alvo_id=str(alvo_id),
        eventos=[_to_out(e) for e in rows],
    )
