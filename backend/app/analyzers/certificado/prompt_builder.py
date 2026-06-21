"""Prompt do extrator de certificado (multimodal → JSON)."""
from __future__ import annotations

OUTPUT_SCHEMA = """
{
  "nome_curso": "<título oficial do curso como está no certificado>",
  "instituicao": "<emissor/escola/plataforma (ex: IMPACTA, Alura, Udemy), ou null>",
  "carga_horaria": "<ex: '40h'. Normalize pra 'Nh'. null se não houver>",
  "data_conclusao": "<YYYY-MM-DD; se só houver ano, YYYY; null se não achar>",
  "aluno": "<nome do aluno no certificado, ou null>",
  "tema": "<UM rótulo: Frontend|Backend|Dados|IA/ML|Infra/Redes|Segurança|Zoho/CRM|Gestão/Soft skills|Outro>",
  "prova": "<1 frase: a competência que este curso comprova>"
}
"""

INSTRUCOES = """
Você lê um CERTIFICADO de conclusão de curso (PDF ou imagem) e extrai os dados
de forma estruturada.

REGRAS:
- Leia o que ESTÁ no documento. NÃO invente. Campo ausente → null.
- "nome_curso": o título oficial; remova sufixos como "(online)" se forem ruído.
- "carga_horaria": normalize pra "Nh" (ex: "40 horas" → "40h"). Se ilegível, null.
- "data_conclusao": prefira a data de conclusão/emissão. Formato YYYY-MM-DD.
- "tema": escolha UM rótulo da lista. Se nenhum casar, "Outro".
- "prova": uma frase curta e útil pra um currículo (o que a pessoa sabe fazer).
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt() -> str:
    return "\n\n".join([
        INSTRUCOES.strip(),
        "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):",
        OUTPUT_SCHEMA.strip(),
    ])
