"""Sugestões de IMAGENS DE CONTEÚDO do post (P5 §6 B-IMG).

Igual à capa, mas pra ilustrar o CORPO: dado o post (título + seções H2),
propõe imagens ancoradas em seções que ficam mais claras com apoio visual.
Cada uma traz prompt em INGLÊS (Imagen), `alt` em PT (acessibilidade/SEO) e a
seção-alvo onde entra. O Pablo escolhe quais gerar — igual nas capas.
"""

OUTPUT_SCHEMA = """
{
  "sugestoes": [
    {
      "secao": "<texto EXATO de um heading H2 do post (copie igual, pra casar)>",
      "conceito": "<rótulo curto do estilo, ex: 'Diagrama de fluxo', 'Cena isométrica'>",
      "descricao": "<1 frase em PT: o que mostra e por que ajuda a entender a seção>",
      "prompt": "<prompt em INGLÊS detalhado pro gerador: assunto + estilo flat/isométrico + composição + paleta. SEM texto/letras/logo na imagem.>",
      "alt": "<alt em português que descreve a imagem (acessibilidade/SEO)>",
      "aspect_ratio": "16:9"
    }
  ]
}
"""

INSTRUCOES = """
Você é diretor de arte do blog da Reative Systems (automação, sistemas e TI pra
PMEs). Para o post abaixo, proponha de 2 a 4 imagens pra ILUSTRAR O CORPO (não a
capa) — cada uma ancorada numa seção H2 que fique mais clara/atraente com um
apoio visual. Cada imagem deve:
- ilustrar o conceito daquela seção (apoio de verdade, não enfeite vazio);
- estilo flat/isométrico, limpo, moderno, profissional (pode usar tons quentes
  da identidade);
- NÃO conter texto, letras, números, logos nem marca d'água.

Para cada uma: `secao` = o texto EXATO de um heading H2 do post (copie igual, pra
casar a inserção), `prompt` em INGLÊS detalhado e autossuficiente, `alt` em
português e `descricao` curta em PT. Não repita a mesma seção. Responda APENAS
com o JSON do schema.
"""


def construir_prompt(
    *,
    title: str,
    secoes: list[str],
    category: str | None = None,
) -> str:
    ctx = [f"Título: {title}"]
    if category:
        ctx.append(f"Categoria: {category}")
    if secoes:
        ctx.append("Seções H2 do post (use o texto EXATO em `secao`):")
        ctx.extend(f"- {s}" for s in secoes)
    else:
        ctx.append("(O post não tem seções H2 claras — sugira mesmo assim e "
                   "deixe `secao` vazio; entra no fim do corpo.)")
    return (
        INSTRUCOES.strip()
        + "\n\n=== POST ===\n"
        + "\n".join(ctx)
        + "\n\n=== FORMATO DE SAÍDA ===\n"
        + OUTPUT_SCHEMA.strip()
    )
