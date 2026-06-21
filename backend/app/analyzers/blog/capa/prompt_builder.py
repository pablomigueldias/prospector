"""Sugestões de CAPA do post (P5 §6 B-IMG).

Dado o conteúdo do post, propõe 3 conceitos DISTINTOS de capa, cada um com um
prompt pronto pro Imagen. O prompt da imagem sai em INGLÊS (Imagen rende melhor
em inglês); a descrição fica em PT pro Pablo escolher.
"""

OUTPUT_SCHEMA = """
{
  "sugestoes": [
    {
      "conceito": "<rótulo curto do estilo, ex: 'Metáfora visual', 'Abstrato geométrico', 'Cena realista'>",
      "descricao": "<1 frase em PT: o que a capa mostra e por que combina com o post>",
      "prompt": "<prompt em INGLÊS pronto pro gerador de imagem, detalhado: assunto, estilo, composição, cores, iluminação. SEM texto/letras na imagem.>",
      "aspect_ratio": "16:9"
    }
  ]
}
"""

INSTRUCOES = """
Você é diretor de arte do blog da Reative Systems (automação, sistemas e TI pra
PMEs). Proponha 3 conceitos DISTINTOS de imagem de CAPA pro post abaixo —
variando a abordagem (ex.: 1 metáfora visual, 1 abstrato/geométrico, 1
cena/ilustração concreta). Cada capa deve:
- combinar com o tema e o tom da marca (moderno, limpo, profissional; pode usar
  tons quentes/terrosos da identidade);
- funcionar como capa de blog (composição boa em 16:9, foco claro);
- NÃO conter texto, letras, números, logos nem marca d'água (capa é só imagem).

Para cada conceito escreva um `prompt` em INGLÊS, detalhado e autossuficiente
(assunto + estilo + composição + paleta + iluminação), e uma `descricao` curta
em PT explicando a ideia. Responda APENAS com o JSON do schema (3 sugestões).
"""


def construir_prompt(
    *,
    title: str,
    excerpt: str | None = None,
    keyword_alvo: str | None = None,
    category: str | None = None,
) -> str:
    ctx = [f"Título: {title}"]
    if category:
        ctx.append(f"Categoria: {category}")
    if keyword_alvo:
        ctx.append(f"Keyword-alvo: {keyword_alvo}")
    if excerpt:
        ctx.append(f"Resumo: {excerpt}")
    return (
        INSTRUCOES.strip()
        + "\n\n=== POST ===\n"
        + "\n".join(ctx)
        + "\n\n=== FORMATO DE SAÍDA ===\n"
        + OUTPUT_SCHEMA.strip()
    )
