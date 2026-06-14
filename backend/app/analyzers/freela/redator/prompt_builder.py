"""Prompt do Redator + Seletor de proposta (freela / Workana).

Gera o RASCUNHO da proposta ancorado no PERFIL MESTRE e seleciona quais
projetos/habilidades destacar. PARA no rascunho: você revisa e envia na mão.
Espelha o redator de candidatura — mesma regra anti-mentira.
"""
from __future__ import annotations

from typing import Optional

from app.analyzers._perfil_texto import perfil_para_texto
from app.api.schemas.pessoal import PerfilMestreResponse


OUTPUT_SCHEMA = """
{
  "texto": "<rascunho COMPLETO da proposta, pronto pra revisar. Siga a estrutura que a Workana recomenda: 1) Apresentação curta e específica; 2) Plano de trabalho em passos (o que você fará); 3) Disponibilidade; 4) Prazo. Cite UM detalhe concreto do projeto pra provar que leu. Tom humano, direto, sem encher linguiça. Sem placeholders tipo [seu nome].>",
  "prazo_sugerido": "<ex: 7 dias>",
  "tom": "<tecnico | institucional>",
  "projetos_destacados": ["<nome EXATO de projeto do perfil, max 3>", "..."],
  "habilidades_destacadas": ["<habilidade EXATA do perfil, max 5>", "..."]
}
"""

INSTRUCOES = """
Você é um freelancer experiente escrevendo uma PROPOSTA pra um projeto numa
plataforma como a Workana. O cliente recebe dezenas de propostas copia-cola —
a sua tem que ser o oposto: específica, ancorada em provas reais e fácil de ler.

Recebe a DESCRIÇÃO DO PROJETO, (quando houver) a ANÁLISE do projeto e o PERFIL
MESTRE do freelancer. Produza:

- "texto": o rascunho da proposta na estrutura Apresentação → Plano de trabalho
  (passos) → Disponibilidade → Prazo. Mencione um detalhe concreto do projeto
  (prova que leu). Proponha um PLANO, não só um preço.
- "prazo_sugerido": um prazo realista pro escopo.
- "tom": "tecnico" se o cliente é técnico, "institucional" se é leigo/empresa.
- "projetos_destacados" e "habilidades_destacadas" (o SELETOR): escolha os que
  MAXIMIZAM relevância PRA ESTE projeto — até 3 projetos e até 5 habilidades,
  com os NOMES EXATOS como aparecem no perfil.

REGRAS (inegociáveis):
- ANTI-MENTIRA: use SOMENTE experiência/projetos/skills que ESTÃO no perfil.
  Reorganize a verdade, nunca invente. Se o perfil não cobre algo que o projeto
  pede, não finja que cobre.
- Não force contato fora da plataforma (a Workana penaliza).
- Não invente preço/valor — quem precifica é outro módulo.
- Português brasileiro, primeira pessoa, sem clichê de "sou apaixonado por...".
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt(
    descricao_projeto: str,
    perfil: PerfilMestreResponse,
    *,
    titulo: Optional[str] = None,
    analise: Optional[dict] = None,
    instrucoes_extra: Optional[str] = None,
) -> str:
    cab = []
    if titulo:
        cab.append(f"Título do projeto: {titulo}")

    bloco_analise = ""
    if analise:
        ganchos = analise.get("ganchos") or []
        requisitos = analise.get("requisitos") or []
        partes = []
        if requisitos:
            partes.append("Requisitos detectados: " + "; ".join(requisitos))
        if ganchos:
            partes.append("Ganchos com o perfil: " + "; ".join(ganchos))
        if partes:
            bloco_analise = "ANÁLISE DO PROJETO:\n" + "\n".join(partes)

    bloco_extra = ""
    if instrucoes_extra:
        bloco_extra = f"INSTRUÇÕES EXTRA DO FREELANCER (atenda): {instrucoes_extra}"

    bloco_projeto = "\n".join(
        cab + ["", "DESCRIÇÃO DO PROJETO (texto colado):", descricao_projeto]
    )

    secoes = [INSTRUCOES.strip(), perfil_para_texto(perfil), bloco_projeto]
    if bloco_analise:
        secoes.append(bloco_analise)
    if bloco_extra:
        secoes.append(bloco_extra)
    secoes += ["FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):", OUTPUT_SCHEMA.strip()]
    return "\n\n".join(secoes)
