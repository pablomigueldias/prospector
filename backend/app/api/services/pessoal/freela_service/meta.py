"""Motor da meta: matemática reversa (meta líquida → valor-hora, projetos e
propostas necessárias, gargalo) + rampa por reputação. Sem IA."""
from __future__ import annotations

import calendar
from datetime import UTC, datetime

from app.api.schemas.freela import (
    FaseRampa,
    PlanoMetaRequest,
    PlanoMetaResponse,
    ProgressoMes,
)
from app.api.services._helpers import r2 as _r2
from app.db.session import get_session
from app.repositories.pessoal.freela_repository import FreelaRepository

from ._base import FreelaError
from .metricas import metricas

# Rampa de meta (líquido/mês). A fase é guiada pela REPUTAÇÃO (nº de fechadas),
# não por R$ — no cold start o gargalo é destravar avaliação, não faturar.
_RAMPA_META = [
    {"nome": "F1 — Cold start", "meta_min": 1500, "meta_max": 2000,
     "foco": "1–2 avaliações 5★ (R$ é secundário); aceitar quick wins"},
    {"nome": "F2 — Tração", "meta_min": 3500, "meta_max": 4500,
     "foco": "subir ticket, parar o fundo de poço, focar no núcleo"},
    {"nome": "F3 — Crescimento", "meta_min": 6500, "meta_max": 7500,
     "foco": "caçar recorrente + gringo/USD; nicho claro"},
    {"nome": "F4 — Meta cheia", "meta_min": 10000, "meta_max": 10000,
     "foco": "renda estável: base recorrente + ticket alto"},
]
# Conversão proposta→fechada baixa o bastante pra ser o gargalo.
_CONVERSAO_FRACA = 0.15
# Semanas por mês (média) pra transformar propostas/mês em propostas/semana.
_SEMANAS_MES = 4.3


async def _progresso_mes(meta_liquida: float) -> ProgressoMes:
    """Realizado no mês corrente vs ritmo linear necessário pra bater a meta.

    Compara o líquido já fechado no mês com a meta proporcional ao dia de hoje
    (ritmo linear). Margem de 10% pros lados pra não acusar "atrás" no dia 2.
    """
    agora = datetime.now(UTC)
    inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    dias_no_mes = calendar.monthrange(agora.year, agora.month)[1]

    async with get_session() as session:
        realizado, fechadas_mes = await FreelaRepository(
            session
        ).soma_liquido_fechado_desde(inicio_mes)

    fracao = agora.day / dias_no_mes
    meta_ate_hoje = _r2(meta_liquida * fracao)

    if fechadas_mes == 0:
        status = "sem_dados"
        resumo = (
            f"Nenhuma fechada ainda neste mês. Pra bater R$ {meta_liquida:.0f}, "
            f"o ritmo pede ~R$ {meta_ate_hoje:.0f} até hoje (dia {agora.day})."
        )
    elif realizado >= meta_ate_hoje * 1.1:
        status = "na_frente"
        resumo = (
            f"Na frente: R$ {realizado:.0f} fechado vs ~R$ {meta_ate_hoje:.0f} "
            f"esperado até o dia {agora.day}. Segue assim."
        )
    elif realizado < meta_ate_hoje * 0.9:
        status = "atras"
        resumo = (
            f"Atrás do ritmo: R$ {realizado:.0f} fechado vs ~R$ {meta_ate_hoje:.0f} "
            f"esperado até hoje. Faltam R$ {max(0, meta_liquida - realizado):.0f} no mês."
        )
    else:
        status = "no_caminho"
        resumo = (
            f"No caminho: R$ {realizado:.0f} fechado, ~R$ {meta_ate_hoje:.0f} "
            f"era o esperado até o dia {agora.day}."
        )

    return ProgressoMes(
        realizado=_r2(realizado),
        meta_ate_hoje=meta_ate_hoje,
        fechadas_mes=fechadas_mes,
        dia=agora.day,
        dias_no_mes=dias_no_mes,
        pct_meta=_r2(realizado / meta_liquida) if meta_liquida else 0.0,
        status=status,
        resumo=resumo,
    )


def _fase_rampa(fechadas: int) -> dict:
    """Fase atual pela reputação: 0 nota = cold start; vai subindo com as fechadas."""
    if fechadas == 0:
        return _RAMPA_META[0]
    if fechadas <= 2:
        return _RAMPA_META[1]
    if fechadas <= 5:
        return _RAMPA_META[2]
    return _RAMPA_META[3]


async def plano_meta(req: PlanoMetaRequest) -> PlanoMetaResponse:
    """Matemática reversa: da meta líquida → valor-hora alvo, projetos e propostas
    necessárias, gargalo e fase da rampa. Reusa as métricas reais."""
    if req.meta_liquida <= 0:
        raise FreelaError("Informe a meta líquida (maior que zero).")
    if req.horas_dia <= 0 or req.dias_mes <= 0 or not (0 < req.pct_faturavel <= 1):
        raise FreelaError("Capacidade inválida (horas/dia, dias/mês, % faturável).")

    m = await metricas()

    horas_faturaveis = _r2(req.horas_dia * req.dias_mes * req.pct_faturavel)
    valor_hora_alvo = _r2(req.meta_liquida / horas_faturaveis) if horas_faturaveis else 0.0

    ticket = m.ticket_medio_fechado or None
    vhr = m.valor_hora_real  # das fechadas
    taxa_fech = m.taxa_fechamento or 0.0

    projetos_mes = _r2(req.meta_liquida / ticket) if ticket else None
    propostas_mes = (
        _r2(projetos_mes / taxa_fech) if (projetos_mes is not None and taxa_fech > 0) else None
    )
    propostas_sem = _r2(propostas_mes / _SEMANAS_MES) if propostas_mes is not None else None

    projecao = _r2(vhr * horas_faturaveis) if vhr else None
    alcancavel = bool(projecao is not None and projecao >= req.meta_liquida)

    # Diagnóstico do gargalo (honesto: prioriza o que mais trava a meta).
    if vhr is None and ticket is None:
        gargalo = "sem_dados"
        diagnostico = (
            f"Feche o 1º projeto pra eu calibrar com seus números. Por ora: pra "
            f"R$ {req.meta_liquida:.0f} líq/mês em {horas_faturaveis:.0f}h faturáveis, "
            f"mire um valor-hora ≥ R$ {valor_hora_alvo:.0f}/h."
        )
    elif vhr is not None and not alcancavel:
        gargalo = "ticket"
        diagnostico = (
            f"Seu valor-hora real (R$ {vhr:.0f}/h) × {horas_faturaveis:.0f}h dá só "
            f"~R$ {projecao:.0f}/mês — não fecha a meta por volume. O caminho é "
            f"SUBIR TICKET (nicho, gringo/USD, recorrente), não pegar mais projeto barato."
        )
    elif taxa_fech and taxa_fech < _CONVERSAO_FRACA:
        gargalo = "conversao"
        diagnostico = (
            f"O R$/h fecha a conta, mas sua conversão é baixa ({taxa_fech*100:.0f}%). "
            f"Foque proposta melhor (checklist) e nos projetos do seu núcleo."
        )
    elif propostas_sem is not None:
        gargalo = "volume"
        diagnostico = (
            f"No seu ritmo, mande ~{propostas_sem:.0f} propostas/semana "
            f"(~{projetos_mes:.0f} projetos/mês a R$ {ticket:.0f} de ticket) pra bater a meta."
        )
    else:
        gargalo = "no_caminho"
        diagnostico = (
            f"Pra R$ {req.meta_liquida:.0f} líq/mês, mire valor-hora ≥ "
            f"R$ {valor_hora_alvo:.0f}/h e mantenha o ritmo de propostas."
        )

    fase = _fase_rampa(m.fechadas)
    progresso = await _progresso_mes(req.meta_liquida)

    return PlanoMetaResponse(
        meta_liquida=_r2(req.meta_liquida),
        horas_faturaveis_mes=horas_faturaveis,
        valor_hora_alvo=valor_hora_alvo,
        valor_hora_real=vhr,
        ticket_medio=ticket,
        projecao_liquida_mes=projecao,
        projetos_necessarios_mes=projetos_mes,
        propostas_necessarias_mes=propostas_mes,
        propostas_por_semana=propostas_sem,
        alcancavel_por_volume=alcancavel,
        gargalo=gargalo,
        diagnostico=diagnostico,
        fase=FaseRampa(**fase),
        progresso_mes=progresso,
    )
