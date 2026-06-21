"""S4 — Agendamentos na UI.

Visão operacional dos jobs do APScheduler: lista cada job com seu horário e se
está ligado (lendo do `settings`, que já reflete os overrides do S3) e permite
**rodar agora** (dispara o job sob demanda). Ligar/desligar e mudar a hora é
feito pela tela via o endpoint do S3 (`/api/config`) — aqui só listamos e
executamos. Mudança de horário/scheduler só vale no próximo restart da API.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings


class AgendamentoError(ValueError):
    """Job desconhecido ou falha ao disparar."""


@dataclass(frozen=True)
class JobDef:
    id: str
    nome: str
    descricao: str
    hora_key: str       # chave de config com a hora (0–23)
    enabled_key: str    # chave de config que liga/desliga


JOBS: tuple[JobDef, ...] = (
    JobDef(
        "rotina_diaria",
        "Rotina diária",
        "Recorrências + lembretes de vencimento + follow-up de freela. "
        "Manda os avisos no Telegram.",
        "lembretes_hora",
        "scheduler_enabled",
    ),
    JobDef(
        "briefing",
        "Resumo da Noite",
        "Briefing noturno (MAS-4): vagas a triar, follow-ups vencendo, "
        "atividades do CRM + 1 micro-ação. Manda no Telegram.",
        "briefing_hora",
        "briefing_enabled",
    ),
)

_POR_ID: dict[str, JobDef] = {j.id: j for j in JOBS}


def listar() -> list[dict]:
    """Cada job com hora, ligado e a chave de config pra a UI editar (via S3)."""
    return [
        {
            "id": j.id,
            "nome": j.nome,
            "descricao": j.descricao,
            "hora": getattr(settings, j.hora_key),
            "ligado": bool(getattr(settings, j.enabled_key)),
            "hora_key": j.hora_key,
            "enabled_key": j.enabled_key,
        }
        for j in JOBS
    ]


async def rodar(job_id: str) -> dict:
    """Dispara o job na hora. Retorna o resultado bruto + quando rodou."""
    job = _POR_ID.get(job_id)
    if job is None:
        raise AgendamentoError(f"job desconhecido: {job_id}")

    if job_id == "rotina_diaria":
        from app.jobs.lembretes import rotina_diaria
        resultado = await rotina_diaria()
    elif job_id == "briefing":
        from app.jobs.briefing import rotina_briefing
        resultado = await rotina_briefing()
    else:  # pragma: no cover — catálogo e dispatch andam juntos
        raise AgendamentoError(f"sem runner pro job: {job_id}")

    return {
        "job": job_id,
        "executado_em": datetime.now(ZoneInfo(settings.timezone)).isoformat(),
        "resultado": resultado,
    }
