"""Smoke do agente Blog (P5 §6.B2) — checklist SEO (determinístico) + parser.

Puro: não toca LLM nem DB (o `redigir` em si depende do Gemini e é exercido
manualmente/na tela). Garante que o gate de SEO pega o essencial e — crucial —
que keyword stuffing vira FAIL. Roda standalone:
    python -m tests.test_blog_seo
"""
from __future__ import annotations

from app.analyzers.blog import checklist_seo as c
from app.analyzers.blog.redator.parser import parse_resposta

_KW = "tirar empresa da planilha"
_CORPO = (
    f"Quer {_KW} sem gastar uma fortuna? Este guia mostra o caminho prático. "
    + "Conteúdo útil e direto pra quem decide. " * 30
    + f"\n\n## Por que {_KW} agora\n\n"
    + "Explicação densa com exemplos reais e sem enrolação. " * 30
    + "Veja nossa [automação sob medida](/servicos/automacao).\n\n"
    + "## O próximo passo\n\n"
    + "Conclusão com um convite pra conversar. " * 30
)


def _post_bom():
    return c.avaliar(
        title=f"Como {_KW} sem gastar muito",
        slug="tirar-empresa-da-planilha",
        keyword_alvo=_KW,
        meta_description=(
            f"Veja como {_KW} sem gastar uma fortuna: sinais, riscos e o caminho "
            "enxuto pra migrar pra um sistema de verdade sem dor de cabeça hoje."
        ),
        excerpt="Um guia direto pra sair do Excel.",
        body_md=_CORPO,
    )


def main() -> None:
    print("━" * 60)
    print("Smoke — agente Blog: checklist SEO + parser (P5 §6.B2)")
    print("━" * 60)

    print("\n→ Test 1: post bem feito tem score alto")
    bom = _post_bom()
    print(f"   score={bom.score} ({bom.nivel}), {len(bom.itens)} itens")
    for i in bom.itens:
        if i.status != "ok":
            print(f"     [{i.status}] {i.id}: {i.label}")
    assert bom.score >= 85, bom.score
    assert bom.nivel in ("bom", "otimo")

    print("\n→ Test 2: keyword stuffing vira FAIL")
    ruim = c.avaliar(
        title="seo seo seo", slug="seo", keyword_alvo="seo",
        meta_description="", body_md="seo " * 100,
    )
    dens = next(i for i in ruim.itens if i.id == "densidade")
    assert dens.status == "fail", dens
    print(f"   densidade=fail, score={ruim.score} ✓")

    print("\n→ Test 3: sem keyword → item crítico falha")
    semkw = c.avaliar(title="Título", body_md="texto " * 300)
    assert any(i.id == "keyword" and i.status == "fail" for i in semkw.itens)
    print("   keyword ausente sinalizada ✓")

    print("\n→ Test 4: parser tolera toc como lista de strings")
    red = parse_resposta(
        '{"title":"T","body_md":"# Oi\\n\\ntexto","keywords":["a"],"toc":["Intro"]}'
    )
    assert red and red.toc[0].label == "Intro", red
    assert parse_resposta("sem json aqui") is None
    print("   parser OK (e rejeita lixo) ✓")

    print("\n✅ Blog SEO/redator OK")


if __name__ == "__main__":
    main()
