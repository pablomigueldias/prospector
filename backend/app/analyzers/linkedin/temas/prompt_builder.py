"""Gera TEMAS de post de tendência pro LinkedIn (P5 §6.C — L2).

Saída: uma lista de {tema, angulo} que depois o redator (L1) transforma em post.
Mantém o foco da `conta` e ancora levemente no que o Pablo realmente domina (pra
o post soar autêntico e não genérico)."""
from app.analyzers._perfil_texto import perfil_para_texto
from app.api.schemas.pessoal import PerfilMestreResponse

OUTPUT_SCHEMA = """
{
  "temas": [
    {"tema": "<assunto específico e atual, não genérico>",
     "angulo": "<o ponto de vista/recorte que torna o post interessante e autêntico>"}
  ]
}
"""

FOCO_REATIVE = (
    "FOCO = PÁGINA DA REATIVE SYSTEMS: tendências de automação, sistemas sob "
    "medida, IA aplicada a negócio, sites e TI pra PMEs — sempre conectando a um "
    "problema real de quem toca uma pequena/média empresa."
)
FOCO_PESSOAL = (
    "FOCO = PERFIL PESSOAL do Pablo (desenvolvedor): tendências de engenharia de "
    "software, IA/LLMs na prática, produtividade de dev, decisões de arquitetura — "
    "do ponto de vista de quem constrói, com opinião técnica honesta."
)


def construir_prompt(
    *,
    quantidade: int,
    conta: str | None = None,
    publico: str | None = None,
    evitar: list[str] | None = None,
    perfil: PerfilMestreResponse | None = None,
) -> str:
    foco = FOCO_PESSOAL if (conta == "pessoal") else FOCO_REATIVE

    bloco_perfil = (
        "STACK/EXPERIÊNCIA DO PABLO (pra os temas serem autênticos, não invente "
        "nada além disto):\n" + perfil_para_texto(perfil)
        if perfil
        else "PERFIL: (indisponível — proponha temas do setor sem citar feitos "
        "específicos do Pablo.)"
    )

    bloco_evitar = ""
    if evitar:
        bloco_evitar = (
            "\n\nNÃO repita temas próximos a estes (já existem):\n"
            + "\n".join(f"- {t}" for t in evitar[:30])
        )

    extra = ""
    if publico:
        extra = f"\nPúblico que queremos atrair: {publico}."

    return (
        f"Você é estrategista de conteúdo de LinkedIn. Gere {quantidade} TEMAS de "
        "post sobre tendências do setor — específicos, atuais e que rendem "
        "engajamento. Nada de tema raso/clichê ('a importância da IA').\n\n"
        + foco
        + extra
        + "\n\n"
        + bloco_perfil
        + bloco_evitar
        + "\n\nResponda APENAS com JSON neste formato:\n"
        + OUTPUT_SCHEMA.strip()
    )
