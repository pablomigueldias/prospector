"""Prompt do Extrator de projeto (freela / Workana).

Recebe o TEXTO COLADO de um projeto da Workana e devolve os campos
estruturados pra pré-preencher o form. Não inventa: o que não achar, deixa null.
"""
from __future__ import annotations


OUTPUT_SCHEMA = """
{
  "titulo": "<título curto do projeto, ou null se não der pra inferir>",
  "faixa_orcamento_min": <número em R$ ou null>,
  "faixa_orcamento_max": <número em R$ ou null>,
  "n_propostas_concorrentes": <inteiro de propostas já feitas, ou null>,
  "n_interessados": <inteiro de interessados, se o texto separar de propostas, ou null>,
  "habilidades": ["<skill/tecnologia exigida explicitamente no texto>", "..."]
}
"""

INSTRUCOES = """
Você extrai dados estruturados do TEXTO de um projeto publicado na Workana.
Devolve só o que estiver EXPLÍCITO ou claramente inferível do texto — nunca
invente número. Regras:

- "titulo": um título curto e fiel ao projeto (se o texto já tiver um, use-o).
- "faixa_orcamento_min"/"max": o orçamento informado, em número inteiro de reais
  (ex.: "R$ 1.000 a R$ 2.500" → min 1000, max 2500). Se houver um valor único,
  use-o nos dois. Se vier em US$, converta NÃO — deixe o número como está e o
  usuário ajusta. Se não houver orçamento, null nos dois.
- "n_propostas_concorrentes": quantas propostas o texto menciona (ex.: "64
  propostas" → 64). Se não mencionar, null.
- "n_interessados": quantos interessados, SE o texto separar isso de propostas.
  Senão, null.
- "habilidades": lista das skills/tecnologias EXIGIDAS que aparecem no texto
  (ex.: "React", "WordPress", "API REST"). Só o que estiver explícito; lista
  vazia se não houver.
- Valores são INTEIROS (sem "R$", sem pontos de milhar). Use null quando faltar.
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt(texto_projeto: str) -> str:
    return "\n\n".join([
        INSTRUCOES.strip(),
        "TEXTO DO PROJETO (colado da Workana):",
        texto_projeto,
        "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):",
        OUTPUT_SCHEMA.strip(),
    ])
