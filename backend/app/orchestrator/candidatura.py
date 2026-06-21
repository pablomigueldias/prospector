"""Cadeia 'Candidatura completa' (MAS-2) — o primeiro coordenador real.

Encadeia os agentes que JÁ existem (vaga.analisar → currículo → candidatura →
checklist), com um **checkpoint humano** entre a análise e as etapas caras de LLM
(a regra de ouro do curso: mostrar os achados e pedir OK antes de gastar tokens).

Cada passo escreve na memória compartilhada (MAS-1) com `origem="coordenador"` —
é assim que os agentes "conversam": o que um faz fica visível na linha do tempo
do alvo pros próximos.
"""
from __future__ import annotations

from app.api.schemas.orchestrator import CandidaturaAnalise, CandidaturaEntrega
from app.api.schemas.pessoal import GerarCandidaturaRequest
from app.api.services import memoria_service
from app.api.services.pessoal import vaga_service

# Abaixo disso o coordenador desaconselha (mas não bloqueia — quem decide é o Pablo).
_LIMIAR_RECOMENDA = 50


async def _mem(vaga_id: str, tipo: str, resumo: str, payload: dict | None = None):
    await memoria_service.registrar(
        agente="coordenador", alvo_tipo="vaga", alvo_id=vaga_id, tipo=tipo,
        resumo=resumo, payload=payload, origem="coordenador",
    )


async def analisar(vaga_id: str) -> CandidaturaAnalise:
    """Fase 1: analisa a vaga e devolve os achados pro checkpoint humano."""
    vaga = await vaga_service.get_vaga(vaga_id)
    res = await vaga_service.analisar_vaga(vaga_id)
    m = res.match
    recomenda = m.aderencia >= _LIMIAR_RECOMENDA

    await _mem(
        vaga_id, "analise",
        f"Vaga analisada: {m.aderencia}% de aderência"
        + (f" — {m.veredito}" if m.veredito else ""),
        {"match_score": res.match_score, "aderencia": m.aderencia,
         "gaps": m.gaps, "recomenda": recomenda},
    )
    return CandidaturaAnalise(
        vaga_id=vaga_id, titulo=vaga.titulo, empresa=vaga.empresa,
        aderencia=m.aderencia, match_score=res.match_score,
        veredito=m.veredito, recomenda=recomenda, gaps=m.gaps,
        destaques=m.destaques, resumo=res.analise.resumo,
    )


def _montar_checklist(gaps: list[str]) -> list[str]:
    itens = [
        "Revisar o CV gerado e cortar o que soar genérico",
        "Conferir a carta e personalizar a saudação (nome de quem recebe)",
    ]
    for g in gaps[:2]:
        itens.append(f"Como vou endereçar o gap: {g}")
    itens += [
        "Atualizar o LinkedIn com as palavras-chave da vaga",
        "Enviar dentro do prazo pelo canal/link oficial da vaga",
    ]
    return itens


async def preparar(vaga_id: str) -> CandidaturaEntrega:
    """Fase 2 (após o OK): gera CV sob medida + carta/e-mail + checklist."""
    cv = await vaga_service.gerar_curriculo(vaga_id)
    await _mem(vaga_id, "curriculo", "CV sob medida gerado pelo coordenador")

    cand = await vaga_service.gerar_candidatura(
        vaga_id, GerarCandidaturaRequest(gerar_carta=True)
    )
    await _mem(vaga_id, "candidatura", "Carta + e-mail de candidatura gerados")

    gaps: list[str] = []
    vaga = await vaga_service.get_vaga(vaga_id)
    if vaga.match_json is not None:
        gaps = vaga.match_json.gaps
    checklist = _montar_checklist(gaps)
    await _mem(vaga_id, "checklist", "Checklist de entrega montado")

    return CandidaturaEntrega(
        vaga_id=vaga_id, curriculo=cv.curriculo, email=cand.email,
        carta=cand.carta, checklist=checklist, rascunho_id=cand.rascunho_id,
    )
