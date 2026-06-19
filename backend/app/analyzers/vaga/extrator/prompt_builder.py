"""Prompt do Extrator de vaga (importar por URL / colar texto).

Recebe o TEXTO de uma vaga (colado ou lido de uma URL) e devolve os campos
estruturados pra pré-preencher o form. Não é a análise/match (esse é o
``analyzers/vaga``) — só extrai o que está EXPLÍCITO. O que não achar, deixa null.
"""
from __future__ import annotations

OUTPUT_SCHEMA = """
{
  "titulo": "<título do cargo, ou null>",
  "empresa": "<nome da empresa que contrata, ou null>",
  "localizacao": "<cidade/UF/país, ou null>",
  "modelo": "<remoto | híbrido | presencial | null>",
  "senioridade": "<júnior | pleno | sênior | estágio | null>"
}
"""

INSTRUCOES = """
Você extrai dados estruturados do TEXTO de uma vaga de emprego (página de um
job board, LinkedIn, Gupy, site da empresa etc.). Devolve só o que estiver
EXPLÍCITO ou claramente inferível — nunca invente. Regras:

- "titulo": o cargo anunciado (ex.: "Desenvolvedor Backend Python Pleno").
- "empresa": quem está contratando. Se o texto não disser, null (não chute o
  job board, ex.: não retorne "LinkedIn"/"Gupy" como empresa).
- "localizacao": cidade/estado/país, se houver.
- "modelo": normalize pra "remoto", "híbrido" ou "presencial". Se não disser, null.
- "senioridade": normalize pra "júnior", "pleno", "sênior" ou "estágio". null se
  não der pra inferir.
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt(texto_vaga: str) -> str:
    return "\n\n".join([
        INSTRUCOES.strip(),
        "TEXTO DA VAGA:",
        texto_vaga,
        "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):",
        OUTPUT_SCHEMA.strip(),
    ])
