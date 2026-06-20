"""Kanban + métricas do pipeline (taxas, ticket, forecast)."""
from __future__ import annotations

from datetime import UTC, datetime

from app.api.schemas.freela import (
    CapacidadeResponse,
    KanbanColuna,
    KanbanResponse,
    MetricasResponse,
    PropostaKanbanItem,
    TaxaPorAnguloItem,
    TaxaPorAnguloResponse,
    TaxaPorStackItem,
    TaxaPorStackResponse,
)
from app.config import settings
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


async def capacidade() -> CapacidadeResponse:
    """Anti-furada: capacidade da semana vs horas já comprometidas (fechadas)."""
    horas_semana = int(settings.freela_capacidade_horas_semana)
    async with get_session() as session:
        comprometidas = await FreelaRepository(session).soma_horas_comprometidas()
    livres = round(max(0.0, horas_semana - comprometidas), 1)
    return CapacidadeResponse(
        horas_semana=horas_semana,
        horas_comprometidas=round(comprometidas, 1),
        horas_livres=livres,
    )


# Status que contam como "o cliente respondeu" (espelha metricas()).
_RESPONDIDAS = {"respondida", "negociando", "fechada"}


def contar_resposta_por_stack(
    linhas: list[tuple[str, dict | None]],
) -> tuple[dict[str, int], dict[str, int], dict[str, int], int, int]:
    """(enviadas, respondidas, fechadas) por stack + totais (enviadas, respondidas).

    Base comum da taxa de resposta/fechamento por stack e da prob. de resposta
    usada no ranking de oportunidades. Ignora rascunhos. `linhas` = (status, analise_json).
    """
    enviadas: dict[str, int] = {}
    respondidas: dict[str, int] = {}
    fechadas: dict[str, int] = {}
    tot_env = tot_resp = 0
    for status, analise in linhas:
        if status == "rascunho":
            continue
        respondeu = status in _RESPONDIDAS
        fechou = status == "fechada"
        tot_env += 1
        if respondeu:
            tot_resp += 1
        for tag in (analise or {}).get("stack") or []:
            chave = str(tag).strip()
            if not chave:
                continue
            enviadas[chave] = enviadas.get(chave, 0) + 1
            if respondeu:
                respondidas[chave] = respondidas.get(chave, 0) + 1
            if fechou:
                fechadas[chave] = fechadas.get(chave, 0) + 1
    return enviadas, respondidas, fechadas, tot_env, tot_resp


async def taxa_por_stack(min_enviadas: int = 2) -> TaxaPorStackResponse:
    """Taxa de resposta E de fechamento por stack/categoria — onde gastar proposta
    rende mais.

    Cruza cada proposta enviada (status != rascunho) com o `stack` do projeto
    (da análise) e mede quantas o cliente respondeu e quantas fecharam. Só mostra
    stacks com pelo menos `min_enviadas` propostas, pra não tirar conclusão de 1.
    """
    async with get_session() as session:
        linhas = await FreelaRepository(session).propostas_status_e_analise()

    enviadas, respondidas, fechadas, _te, _tr = contar_resposta_por_stack(linhas)

    itens = [
        TaxaPorStackItem(
            stack=tag,
            enviadas=env,
            respondidas=respondidas.get(tag, 0),
            taxa_resposta=_r2(respondidas.get(tag, 0) / env),
            fechadas=fechadas.get(tag, 0),
            win_rate=_r2(fechadas.get(tag, 0) / env),
        )
        for tag, env in enviadas.items()
        if env >= min_enviadas
    ]
    # Onde insistir primeiro: maior win-rate, desempate por taxa de resposta e volume.
    itens.sort(key=lambda i: (-i.win_rate, -i.taxa_resposta, -i.enviadas))
    return TaxaPorStackResponse(itens=itens)


async def taxa_por_angulo() -> TaxaPorAnguloResponse:
    """Taxa de resposta por ângulo de abertura (A/B) — qual 1ª linha converte.

    Cruza cada proposta enviada (status != rascunho, com ângulo marcado) com o
    fato de o cliente ter respondido. Sem amostra mínima aqui: são só 3 ângulos.
    """
    async with get_session() as session:
        linhas = await FreelaRepository(session).propostas_status_e_angulo()

    enviadas: dict[str, int] = {}
    respondidas: dict[str, int] = {}
    for status, angulo in linhas:
        if status == "rascunho" or not angulo:
            continue
        enviadas[angulo] = enviadas.get(angulo, 0) + 1
        if status in _RESPONDIDAS:
            respondidas[angulo] = respondidas.get(angulo, 0) + 1

    itens = [
        TaxaPorAnguloItem(
            angulo=ang,
            enviadas=env,
            respondidas=respondidas.get(ang, 0),
            taxa_resposta=_r2(respondidas.get(ang, 0) / env),
        )
        for ang, env in enviadas.items()
    ]
    itens.sort(key=lambda i: (-i.taxa_resposta, -i.enviadas))
    return TaxaPorAnguloResponse(itens=itens)
