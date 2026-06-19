"""Briefing noturno (MAS-4) — o coordenador em modo proativo.

Monta o 'Resumo da Noite' triando o que precisa de você: vagas novas pra triar,
follow-ups de freela vencendo, atividades do CRM pendentes/atrasadas e UMA
micro-ação sugerida. **Não envia nada pra fora** — só prepara; quem decide é o
Pablo (governança: supervisão humana). Ver docs/plano-agentes-autonomos.md (MAS-4).
"""
from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import select

from app.api.schemas.orchestrator import Briefing, BriefingItem
from app.api.services import crm_service
from app.api.services.pessoal import vaga_service
from app.config import settings
from app.db.models.pessoal.freela.cliente import Cliente
from app.db.models.pessoal.freela.projeto import Projeto
from app.db.models.pessoal.freela.proposta import Proposta
from app.db.session import get_session


async def _vagas_triar() -> BriefingItem:
    resp = await vaga_service.listar_vagas()
    pendentes = [v for v in resp.items if not v.tem_analise]
    ex = [
        v.titulo + (f" ({v.empresa})" if v.empresa else "")
        for v in pendentes[:5]
    ]
    return BriefingItem(total=len(pendentes), exemplos=ex)


async def _freela_followups() -> BriefingItem:
    dias = settings.freela_followup_dias
    agora = datetime.now(UTC)
    async with get_session() as session:
        linhas = (await session.execute(
            select(Proposta, Projeto.titulo, Cliente.nome)
            .join(Projeto, Projeto.id == Proposta.projeto_id)
            .outerjoin(Cliente, Cliente.id == Projeto.cliente_id)
            .where(
                Proposta.status == "enviada",
                Proposta.data_resposta.is_(None),
                Proposta.enviada_em.is_not(None),
            )
            .order_by(Proposta.enviada_em.asc())
        )).all()
    ex: list[str] = []
    total = 0
    for proposta, titulo, cliente in linhas:
        enviada = proposta.enviada_em
        if enviada.tzinfo is None:
            enviada = enviada.replace(tzinfo=UTC)
        d = (agora - enviada).days
        if d >= dias:
            total += 1
            if len(ex) < 5:
                quem = f" — {cliente}" if cliente else ""
                ex.append(f"{titulo}{quem} (há {d}d)")
    return BriefingItem(total=total, exemplos=ex)


def _micro_acao(vagas: BriefingItem, freela: BriefingItem, atrasadas: int) -> str:
    if atrasadas > 0:
        return "Resolva 1 atividade atrasada do CRM (a mais antiga)."
    if freela.total > 0:
        return f"Dê 1 follow-up na Workana: {freela.exemplos[0] if freela.exemplos else 'proposta mais antiga'}."
    if vagas.total > 0:
        return f"Triague 1 vaga nova: {vagas.exemplos[0] if vagas.exemplos else 'a primeira da lista'}."
    return "Tudo triado. Use 15min pra 1 micro-ação de LinkedIn (1 comentário relevante)."


def _montar_texto(b: Briefing) -> str:
    linhas = [f"🌙 <b>Resumo da Noite</b> — {b.data}", ""]
    linhas.append(f"🎯 Vagas pra triar: <b>{b.vagas_triar.total}</b>")
    for e in b.vagas_triar.exemplos[:3]:
        linhas.append(f"   • {e}")
    linhas.append(f"📨 Follow-ups freela: <b>{b.freela_followups.total}</b>")
    for e in b.freela_followups.exemplos[:3]:
        linhas.append(f"   • {e}")
    linhas.append(
        f"📋 CRM: {b.atividades_pendentes} pendente(s), "
        f"{b.atividades_atrasadas} atrasada(s)"
    )
    linhas.append("")
    linhas.append(f"👉 <b>Micro-ação:</b> {b.micro_acao}")
    return "\n".join(linhas)


async def gerar() -> Briefing:
    vagas = await _vagas_triar()
    freela = await _freela_followups()
    dash = await crm_service.dashboard()

    b = Briefing(
        data=date.today().isoformat(),
        vagas_triar=vagas,
        freela_followups=freela,
        atividades_pendentes=dash.atividades_pendentes,
        atividades_atrasadas=dash.atividades_atrasadas,
    )
    b.micro_acao = _micro_acao(vagas, freela, dash.atividades_atrasadas)
    b.texto = _montar_texto(b)
    return b
