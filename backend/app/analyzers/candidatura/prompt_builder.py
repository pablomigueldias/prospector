"""Prompt que rascunha o e-mail de candidatura + carta de apresentação.

Espelha o copywriter do Prospector, mas no SEU tom e pra uma vaga. Os dois
princípios inegociáveis valem aqui:
  1. A ferramenta PARA no rascunho — este prompt só escreve, não envia.
  2. REORGANIZA a verdade, nunca INVENTA — proibido criar experiência que
     não está no Perfil Mestre.
"""
from __future__ import annotations

from typing import Optional

from app.api.schemas.pessoal import (
    AnaliseVaga,
    MatchVaga,
    PerfilMestreResponse,
)
from app.analyzers._perfil_texto import (
    blocos_curriculo_para_texto,
    perfil_para_texto,
)


OUTPUT_SCHEMA_COM_CARTA = """
{
  "email": {
    "assunto": "<assunto objetivo, máx 70 caracteres>",
    "corpo": "<corpo do e-mail de candidatura, com quebras de linha reais>",
    "tom": "<2-3 palavras descrevendo o tom>"
  },
  "variantes_email": [
    {
      "assunto": "<assunto alternativo>",
      "corpo": "<corpo alternativo, ângulo diferente>",
      "tom": "<tom da variante>"
    }
  ],
  "carta": {
    "corpo": "<carta de apresentação mais longa e formal que o e-mail>",
    "tom": "<2-3 palavras descrevendo o tom>"
  }
}
"""

OUTPUT_SCHEMA_SEM_CARTA = """
{
  "email": {
    "assunto": "<assunto objetivo, máx 70 caracteres>",
    "corpo": "<corpo do e-mail de candidatura, com quebras de linha reais>",
    "tom": "<2-3 palavras descrevendo o tom>"
  },
  "variantes_email": [
    {
      "assunto": "<assunto alternativo>",
      "corpo": "<corpo alternativo, ângulo diferente>",
      "tom": "<tom da variante>"
    }
  ],
  "carta": null
}
"""

INSTRUCOES = """
Você ajuda ESTE candidato a escrever a candidatura dele pra uma vaga
específica. Escreve em PRIMEIRA PESSOA, como se fosse o próprio candidato.

REGRAS INEGOCIÁVEIS:
1. NUNCA INVENTE. Use só o que está no Perfil Mestre. Proibido criar
   experiência, empresa, anos ou tecnologia que não estão lá. Se a vaga
   pede algo que o candidato não tem, NÃO finja que tem — no máximo,
   demonstre disposição honesta de aprender, sem prometer experiência.
2. ESCREVA NO TOM DO CANDIDATO. Use o bloco "TOM DE ESCRITA" como
   referência de voz. Não soe como IA genérica nem como manual de RH.

REGRAS DE QUALIDADE:
3. PERSONALIZE pra esta vaga: cite o que a análise apontou como requisito
   e conecte com o que o candidato COMPROVADAMENTE tem (use os "destaques").
4. VALOR ANTES DE PEDIR: mostre fit nos primeiros parágrafos.
5. CURTO no e-mail: máx ~160 palavras. A carta pode ser mais longa.
6. SEM exagero ("melhor do mercado", "revolucionário"). Sem clichê de
   vendas ("venho por meio desta", "espero que esta mensagem o encontre bem").
7. Um CTA leve no fim (disponibilidade pra conversar).
8. Português brasileiro.
9. Gere o e-mail principal + 2 variantes de e-mail com ângulos diferentes.

Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def _bloco_vaga(
    titulo: str,
    empresa: Optional[str],
    analise: Optional[AnaliseVaga],
    match: Optional[MatchVaga],
) -> str:
    linhas = ["VAGA-ALVO:", f"- Título: {titulo}"]
    if empresa:
        linhas.append(f"- Empresa: {empresa}")

    if analise:
        if analise.resumo:
            linhas.append(f"- Resumo da vaga: {analise.resumo}")
        if analise.requisitos_obrigatorios:
            linhas.append(
                "- Requisitos obrigatórios: "
                + "; ".join(analise.requisitos_obrigatorios)
            )
        if analise.desejaveis:
            linhas.append("- Desejáveis: " + "; ".join(analise.desejaveis))
        if analise.stack:
            linhas.append("- Stack: " + ", ".join(analise.stack))

    if match:
        if match.destaques:
            linhas.append(
                "\nDESTAQUES A ENFATIZAR (já validados contra o perfil): "
                + "; ".join(match.destaques)
            )
        if match.tenho:
            linhas.append("PONTOS FORTES x vaga: " + "; ".join(match.tenho))
        if match.gaps:
            linhas.append(
                "GAPS (NÃO minta sobre eles; no máximo mostre disposição): "
                + "; ".join(match.gaps)
            )
    return "\n".join(linhas)


def construir_prompt(
    perfil: PerfilMestreResponse,
    *,
    titulo: str,
    empresa: Optional[str] = None,
    analise: Optional[AnaliseVaga] = None,
    match: Optional[MatchVaga] = None,
    gerar_carta: bool = True,
    instrucoes_extra: Optional[str] = None,
) -> str:
    partes = [
        INSTRUCOES.strip(),
        perfil_para_texto(perfil),
    ]

    if perfil.tom_escrita:
        partes.append("TOM DE ESCRITA (imite esta voz):\n" + perfil.tom_escrita)

    blocos = blocos_curriculo_para_texto(perfil)
    if blocos:
        partes.append(blocos)

    partes.append(_bloco_vaga(titulo, empresa, analise, match))

    if instrucoes_extra:
        partes.append("AJUSTES PEDIDOS PRA ESTA CANDIDATURA:\n" + instrucoes_extra)

    schema = OUTPUT_SCHEMA_COM_CARTA if gerar_carta else OUTPUT_SCHEMA_SEM_CARTA
    partes.append("FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):")
    partes.append(schema.strip())

    return "\n\n".join(partes)
