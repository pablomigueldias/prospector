"""Cadeia 'Proposta de freela' — o coordenador do freela (P1 do PLANO-MESTRE).

Espelha a cadeia de candidatura (MAS-2), mas pro Workana: analisa o projeto →
**[checkpoint humano: vale gastar proposta aqui?]** → cota + redige + confere a
proposta. Reusa os services que já existem (`analisar_projeto`, `criar_proposta`,
`redigir_proposta`, `avaliar_proposta`) — é coordenação por cima, não reescrita.

Cada passo grava na memória compartilhada (MAS-1) com `origem="coordenador"` na
timeline do projeto (`alvo_tipo="freela"`), pra os agentes "conversarem".
"""
from __future__ import annotations

from app.api.schemas.freela import AnaliseFreela, PropostaCreate, RedigirRequest
from app.api.schemas.orchestrator import (
    PropostaFreelaAnalise,
    PropostaFreelaEntrega,
)
from app.api.services import memoria_service
from app.api.services.pessoal import freela_service

# Abaixo disso o coordenador desaconselha gastar a proposta (não bloqueia).
_LIMIAR_FIT = 50


async def _mem(projeto_id: str, tipo: str, resumo: str, payload: dict | None = None):
    await memoria_service.registrar(
        agente="coordenador", alvo_tipo="freela", alvo_id=projeto_id, tipo=tipo,
        resumo=resumo, payload=payload, origem="coordenador",
    )


async def analisar(projeto_id: str) -> PropostaFreelaAnalise:
    """Fase 1: analisa o projeto e devolve os achados pro checkpoint humano."""
    proj = await freela_service.get_projeto(projeto_id)
    res = await freela_service.analisar_projeto(projeto_id)
    a = res.analise
    e = a.estimativa

    recomenda = (
        (a.fit_score or 0) >= _LIMIAR_FIT
        and (a.recomendacao or "").lower() != "evite"
        and (a.risco or "").lower() != "alto"
    )

    await _mem(
        projeto_id, "analise",
        f"Projeto analisado: fit {a.fit_score}%"
        + (f" — {a.veredito}" if a.veredito else ""),
        {"fit_score": a.fit_score, "quadrante": a.quadrante,
         "recomenda": recomenda,
         "valor_sugerido": e.valor_sugerido if e else None},
    )
    return PropostaFreelaAnalise(
        projeto_id=projeto_id, titulo=proj.titulo,
        fit_score=a.fit_score or 0, recomendacao=a.recomendacao, risco=a.risco,
        quadrante=a.quadrante, veredito=a.veredito,
        veredito_preco=a.veredito_preco, recomenda=recomenda,
        tarefas=a.tarefas, perguntas_cliente=a.perguntas_cliente,
        skills_faltando=a.skills_faltando, estimativa=e,
    )


async def preparar(projeto_id: str) -> PropostaFreelaEntrega:
    """Fase 2 (após o OK): cota (da análise salva), redige e confere a proposta."""
    proj = await freela_service.get_projeto(projeto_id)
    analise = (
        AnaliseFreela.model_validate(proj.analise_json)
        if proj.analise_json else None
    )
    e = analise.estimativa if analise else None
    valor = float(e.valor_sugerido) if e and e.valor_sugerido is not None else None
    horas = float(e.horas_estimadas) if e and e.horas_estimadas is not None else None
    prazo = f"{e.prazo_dias} dias" if e and e.prazo_dias else None

    # Reusa a proposta mais recente do projeto, ou cria uma com a cotação da análise.
    existentes = await freela_service.listar_propostas_do_projeto(projeto_id)
    if existentes:
        proposta_id = existentes[0].id
    else:
        nova = await freela_service.criar_proposta(
            PropostaCreate(
                projeto_id=projeto_id, valor_cotado=valor,
                horas_estimadas=horas, prazo_proposto=prazo,
            )
        )
        proposta_id = nova.id
    await _mem(
        projeto_id, "precificacao",
        f"Proposta preparada — cotar R$ {valor:.0f}" if valor else "Proposta preparada",
        {"valor_cotado": valor, "horas": horas, "prazo": prazo},
    )

    red = await freela_service.redigir_proposta(proposta_id, RedigirRequest())
    await _mem(projeto_id, "rascunho", "Rascunho da proposta gerado pelo coordenador")

    chk = await freela_service.avaliar_proposta(proposta_id)
    await _mem(
        projeto_id, "checklist",
        f"Checklist: {chk.score}/100" + (f" ({chk.selo})" if chk.selo else ""),
        {"score": chk.score, "selo": chk.selo},
    )

    return PropostaFreelaEntrega(
        projeto_id=projeto_id, proposta_id=proposta_id,
        valor_cotado=valor, horas_estimadas=horas, prazo=prazo,
        texto=red.redacao.texto,
        variacoes_abertura=red.redacao.variacoes_abertura,
        checklist_score=chk.score, checklist_selo=chk.selo,
        checklist_sugestoes=chk.sugestoes,
    )
