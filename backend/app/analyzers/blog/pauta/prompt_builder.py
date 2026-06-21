"""Motor de pauta do blog (P5 §6.B3).

Gera/ranqueia um BACKLOG de pautas a partir de 3 fontes:
(a) PROJETOS feitos (Perfil Mestre → viram case/prova),
(b) SEO/palavras-chave (o que PME/recrutador/cliente busca no Google),
(c) TENDÊNCIAS do setor (IA/automação/dados).
Cada pauta sai com keyword-alvo, intenção, público e estágio de funil, e um
score de prioridade (impacto×esforço). Anti-mentira: pauta de case só sobre o
que ESTÁ no perfil.
"""
from app.analyzers._perfil_texto import perfil_para_texto
from app.api.schemas.pessoal import PerfilMestreResponse

OUTPUT_SCHEMA = """
{
  "pautas": [
    {
      "titulo": "<título de trabalho da pauta, específico e atraente>",
      "resumo": "<1-2 frases: o ângulo e por que vale (a quem ajuda, o que entrega)>",
      "keyword_alvo": "<keyword primária que essa pauta deveria ranquear>",
      "intencao": "informacional | comercial | navegacional",
      "publico": "cliente | recrutador",
      "estagio_funil": "topo | meio | fundo",
      "fonte": "projeto | seo | tendencia",
      "score": <0-100, prioridade = impacto (tráfego/conversão) ÷ esforço>
    }
  ]
}
"""

INSTRUCOES = """
Você é o estrategista de conteúdo da Reative Systems — empresa de automação,
sistemas sob medida, sites e suporte de TI pra PMEs. Sua tarefa: propor PAUTAS
de blog que (a) ranqueiem no Google pra atrair CLIENTE e RECRUTADOR e (b) provem
competência. Conteúdo útil de verdade, nunca clickbait vazio.

Gere pautas distribuídas entre as 3 FONTES:
- "projeto": vira CASE — baseada em algo REAL do PERFIL MESTRE (um projeto/skill
  do Pablo). NÃO invente projeto, cliente, número ou resultado que não esteja no
  perfil. Se o perfil é magro, gere menos pautas de projeto.
- "seo": responde a uma busca que o público-alvo faz no Google (dor, dúvida,
  comparação, "quanto custa", "como escolher"). Pense em intenção e funil.
- "tendencia": tema quente do setor (IA aplicada a PME, automação, dados)
  conectado ao que a Reative faz.

Para cada pauta dê: titulo, resumo (ângulo), keyword_alvo, intencao, publico,
estagio_funil e um score 0-100 de prioridade (alто = muito tráfego/conversão e
pouco esforço pra escrever bem; score alto = vale priorizar). Ordene por score.

REGRAS:
- Pautas DISTINTAS entre si e DIFERENTES das que já existem (listadas abaixo).
- Específicas e acionáveis — nada de "Os benefícios da tecnologia".
- Português brasileiro. Responda APENAS com JSON do schema. Sem texto fora dele.
"""


def construir_prompt(
    *,
    quantidade: int = 6,
    fontes: list[str] | None = None,
    publico: str | None = None,
    sementes: str | None = None,
    tendencias: str | None = None,
    perfil: PerfilMestreResponse | None = None,
    titulos_existentes: list[str] | None = None,
) -> str:
    pedido = [f"Gere {quantidade} pautas."]
    if fontes:
        pedido.append("Use SOMENTE estas fontes: " + ", ".join(fontes) + ".")
    if publico:
        pedido.append(f"Priorize o público: {publico}.")
    if sementes:
        pedido.append(f"Temas/keywords que o Pablo quer mirar: {sementes}")
    if tendencias:
        pedido.append(f"Tendências a considerar: {tendencias}")

    bloco_perfil = (
        "PERFIL MESTRE (base das pautas de 'projeto' — não invente nada além disto):\n"
        + perfil_para_texto(perfil)
        if perfil
        else "PERFIL MESTRE: (indisponível — gere poucas/nenhuma pauta 'projeto')."
    )

    existentes = ""
    if titulos_existentes:
        existentes = "PAUTAS JÁ NO BACKLOG (NÃO repita nem pareça com estas):\n" + "\n".join(
            f"- {t}" for t in titulos_existentes[:40]
        )

    partes = [INSTRUCOES.strip(), "=== PEDIDO ===\n" + "\n".join(pedido), bloco_perfil]
    if existentes:
        partes.append(existentes)
    partes.append("=== FORMATO DE SAÍDA ===\n" + OUTPUT_SCHEMA.strip())
    return "\n\n".join(partes)
