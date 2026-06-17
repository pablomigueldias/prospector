"""Kanban + métricas do pipeline (taxas, ticket, forecast)."""
from __future__ import annotations

from datetime import UTC, datetime

from app.api.schemas.freela import (
    KanbanColuna,
    KanbanResponse,
    MetricasResponse,
    PropostaKanbanItem,
)
from app.api.services._helpers import r2 as _r2
from app.db.models.pessoal.freela.proposta import STATUS_PROPOSTA
from app.db.session import get_session
from app.repositories.pessoal.freela_repository import FreelaRepository

from ._base import _iso


def _dias_desde(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    agora = datetime.now(UTC)
    base = dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    return (agora - base).days


async def kanban() -> KanbanResponse:
    async with get_session() as session:
        linhas = await FreelaRepository(session).listar_propostas_kanban()

    por_status: dict[str, list[PropostaKanbanItem]] = {s: [] for s in STATUS_PROPOSTA}
    for proposta, projeto_titulo, cliente_nome in linhas:
        ref = proposta.enviada_em or proposta.created_at
        por_status.setdefault(proposta.status, []).append(
            PropostaKanbanItem(
                id=str(proposta.id),
                projeto_id=str(proposta.projeto_id),
                projeto_titulo=projeto_titulo,
                cliente_nome=cliente_nome,
                valor_cotado=float(proposta.valor_cotado) if proposta.valor_cotado is not None else None,
                valor_liquido_estimado=float(proposta.valor_liquido_estimado) if proposta.valor_liquido_estimado is not None else None,
                status=proposta.status,
                dias_desde_envio=_dias_desde(ref),
                created_at=_iso(proposta.created_at),
            )
        )
    colunas = [KanbanColuna(status=s, items=por_status.get(s, [])) for s in STATUS_PROPOSTA]
    return KanbanResponse(colunas=colunas)


async def metricas() -> MetricasResponse:
    async with get_session() as session:
        repo = FreelaRepository(session)
        contagem = await repo.contar_por_status()
        liquido_total, qtd_fechadas = await repo.soma_liquido_fechado()
        pipeline_aberto, qtd_aberto = await repo.soma_liquido_em_aberto()
        tempo_resposta = await repo.tempo_medio_resposta_horas()
        valor_hora_real = await repo.valor_hora_real_fechadas()

    total = sum(contagem.values())
    # "enviadas" = tudo que saiu da gaveta (qualquer status menos rascunho).
    enviadas = total - contagem.get("rascunho", 0)
    respondidas = (
        contagem.get("respondida", 0)
        + contagem.get("negociando", 0)
        + contagem.get("fechada", 0)
    )
    fechadas = contagem.get("fechada", 0)
    perdidas = contagem.get("perdida", 0)

    taxa_resposta = _r2(respondidas / enviadas) if enviadas else 0.0
    taxa_fechamento = _r2(fechadas / enviadas) if enviadas else 0.0
    ticket_medio = _r2(liquido_total / qtd_fechadas) if qtd_fechadas else 0.0

    # Forecast: o que provavelmente entra do pipeline em aberto. Ponderado pela
    # sua taxa de fechamento histórica; sem histórico ainda, assume 50% (chute
    # neutro) pra não mostrar R$0 e dar uma referência.
    prob = taxa_fechamento if fechadas else 0.5
    forecast = _r2(pipeline_aberto * prob)

    return MetricasResponse(
        total_propostas=total,
        enviadas=enviadas,
        respondidas=respondidas,
        fechadas=fechadas,
        perdidas=perdidas,
        em_aberto=qtd_aberto,
        taxa_resposta=taxa_resposta,
        taxa_fechamento=taxa_fechamento,
        liquido_total_fechado=_r2(liquido_total),
        ticket_medio_fechado=ticket_medio,
        pipeline_aberto_liquido=_r2(pipeline_aberto),
        forecast_liquido=forecast,
        tempo_medio_resposta_horas=tempo_resposta,
        valor_hora_real=valor_hora_real,
    )
