"""Prompt que destrincha a vaga e cruza com o Perfil Mestre.

Espelha o ``analyzers/gemini/prompt_builder`` do Prospector, mas em vez
de analisar uma empresa, analisa uma vaga (Fase 2) e calcula o match
com você (Fase 3) numa única chamada.
"""
from __future__ import annotations

from typing import Optional

from app.api.schemas.pessoal import PerfilMestreResponse
from app.analyzers._perfil_texto import perfil_para_texto


OUTPUT_SCHEMA = """
{
  "analise": {
    "requisitos_obrigatorios": ["<requisito must-have>", "..."],
    "desejaveis": ["<diferencial/nice-to-have>", "..."],
    "stack": ["<tecnologia citada>", "..."],
    "senioridade": "<júnior | pleno | sênior | não informado>",
    "palavras_chave": ["<termo que o ATS/recrutador busca>", "..."],
    "resumo": "<2-3 frases: o que a vaga realmente quer>"
  },
  "match": {
    "aderencia": <inteiro 0-100>,
    "tenho": ["<requisito da vaga que o candidato CLARAMENTE atende, com a prova>", "..."],
    "gaps": ["<requisito que falta ou precisa estudar/mencionar com cuidado>", "..."],
    "destaques": ["<projeto/skill do perfil a enfatizar NESTA vaga>", "..."],
    "veredito": "<1 frase: vale o esforço de se candidatar? por quê?>"
  }
}
"""

INSTRUCOES = """
Você é um analista técnico de recrutamento. Recebe a DESCRIÇÃO DE UMA VAGA
e o PERFIL MESTRE de um candidato. Sua tarefa tem duas partes:

PARTE 1 — DESTRINCHAR A VAGA (campo "analise"):
- Separe requisitos OBRIGATÓRIOS dos DESEJÁVEIS. Se a vaga não deixa claro,
  use o bom senso (linguagem como "imprescindível"/"obrigatório" vs
  "diferencial"/"é um plus").
- Liste a stack/tecnologias citadas explicitamente.
- Extraia palavras-chave que um recrutador ou ATS buscaria.
- Resuma em 2-3 frases o que a vaga realmente procura.

PARTE 2 — CRUZAR COM O CANDIDATO (campo "match"):
- "aderencia": um número 0-100 honesto de quão fit o candidato é.
- "tenho": só o que o perfil COMPROVA. Cite a prova (projeto/experiência).
  NÃO invente experiência que não está no perfil.
- "gaps": o que a vaga pede e o perfil não evidencia. Seja franco — isto
  serve pra decidir se vale o esforço e o que estudar.
- "destaques": o que do perfil merece destaque NESTA vaga específica
  (reorganizar a verdade, nunca inventá-la).
- "veredito": uma frase dizendo se vale a pena se candidatar.

REGRAS:
- Seja honesto no score. Inflar aderência não ajuda o candidato.
- Baseie "tenho" e "destaques" SOMENTE no que está no perfil.
- Português brasileiro.
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt(
    descricao_vaga: str,
    perfil: PerfilMestreResponse,
    *,
    titulo: Optional[str] = None,
    empresa: Optional[str] = None,
) -> str:
    cabecalho = []
    if titulo:
        cabecalho.append(f"Título da vaga: {titulo}")
    if empresa:
        cabecalho.append(f"Empresa: {empresa}")
    bloco_vaga = "\n".join(cabecalho + ["", "DESCRIÇÃO DA VAGA:", descricao_vaga])

    return "\n\n".join([
        INSTRUCOES.strip(),
        perfil_para_texto(perfil),
        bloco_vaga,
        "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):",
        OUTPUT_SCHEMA.strip(),
    ])
