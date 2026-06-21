"""Smoke do motor de pauta (P5 §6.B3) — parser + CRUD/dedup.

A geração via LLM é exercida manualmente/na tela; aqui foca no que é
determinístico: o parser (normaliza/valida) e o CRUD das pautas. Precisa do
Postgres de dev migrado. Roda standalone:
    python -m tests.test_blog_pauta
"""
from __future__ import annotations

import asyncio

from app.analyzers.blog.pauta.parser import parse_resposta
from app.api.schemas.blog import BlogPautaManualCreate, BlogPautaUpdate
from app.api.services import blog_service as svc

_TITULO = "Teste Pauta B3 (smoke)"


def _unit_parser() -> None:
    print("\n→ Test 1: parser normaliza e valida")
    cru = """{"pautas":[
      {"titulo":"Vale a pena automatizar?","keyword_alvo":"automatizar pme",
       "intencao":"comercial","publico":"cliente","estagio_funil":"meio",
       "fonte":"seo","score":120},
      {"titulo":"","fonte":"seo"},
      {"titulo":"Case real","fonte":"INVALIDA","intencao":"xpto","score":"abc"}
    ]}"""
    pautas = parse_resposta(cru)
    assert len(pautas) == 2, pautas  # a sem título é descartada
    assert pautas[0]["score"] == 100, "score clampa em 100"
    assert pautas[1]["fonte"] == "seo", "fonte inválida cai no default"
    assert pautas[1]["intencao"] is None, "intenção inválida vira None"
    assert parse_resposta("nada de json") == []
    print("   clamp/dedup-de-campos/fallback OK ✓")


async def _crud() -> None:
    # limpa execução anterior
    for p in await svc.pauta.listar():
        if p.titulo == _TITULO:
            await svc.pauta.deletar(p.id)

    print("\n→ Test 2: CRUD da pauta manual")
    p = await svc.pauta.criar_manual(
        BlogPautaManualCreate(titulo=_TITULO, keyword_alvo="kw", publico="cliente")
    )
    assert p.fonte == "manual" and p.status == "ideia" and p.score == 0
    print("   criada (fonte=manual, ideia) ✓")

    achou = [x for x in await svc.pauta.listar(status="ideia") if x.id == p.id]
    assert achou, "não apareceu na lista por status"

    up = await svc.pauta.atualizar(p.id, BlogPautaUpdate(status="escolhida", score=80))
    assert up.status == "escolhida" and up.score == 80
    print("   atualizada (escolhida, score 80) ✓")

    await svc.pauta.deletar(p.id)
    assert all(x.id != p.id for x in await svc.pauta.listar())
    print("   apagada ✓")


def main() -> None:
    print("━" * 60)
    print("Smoke — motor de pauta do blog (P5 §6.B3)")
    print("━" * 60)
    _unit_parser()
    asyncio.run(_crud())
    print("\n✅ Blog pauta OK")


if __name__ == "__main__":
    main()
