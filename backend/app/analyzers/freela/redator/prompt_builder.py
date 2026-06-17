"""Prompt do Redator + Seletor de proposta (freela / Workana).

Gera o RASCUNHO da proposta ancorado no PERFIL MESTRE e seleciona quais
projetos/habilidades destacar. PARA no rascunho: você revisa e envia na mão.
Espelha o redator de candidatura — mesma regra anti-mentira.
"""
from __future__ import annotations

from app.analyzers._perfil_texto import perfil_para_texto
from app.api.schemas.pessoal import PerfilMestreResponse

OUTPUT_SCHEMA = """
{
  "texto": "<rascunho COMPLETO da proposta, pronto pra revisar. Siga a estrutura que a Workana recomenda: 1) Apresentação curta e específica; 2) Plano de trabalho em passos (o que você fará); 3) Disponibilidade; 4) Prazo. Cite UM detalhe concreto do projeto pra provar que leu. Tom humano, direto, sem encher linguiça. Sem placeholders tipo [seu nome].>",
  "prazo_sugerido": "<ex: 7 dias>",
  "tom": "<tecnico | institucional>",
  "projetos_destacados": ["<nome EXATO de projeto do perfil, max 3>", "..."],
  "habilidades_destacadas": ["<habilidade EXATA do perfil, max 5>", "..."],
  "variacoes_abertura": ["<1ª frase/abertura alternativa, ângulo diferente>", "<outra>", "<outra>"]
}
"""

COLD_START = """
MODO COLD START (o freelancer ainda NÃO tem avaliações nesta plataforma):
Sem nota, o cliente desconfia — a proposta tem que COMPENSAR isso. Faça:
1) PROVA por descrição: em vez de só citar projetos, descreva 1 resultado real
   do perfil no formato problema → o que fez → impacto. O impacto é QUALITATIVO
   quando não há número medido no perfil — NÃO invente percentual/estatística pra
   preencher. Pode remeter a "meus projetos no meu perfil/portfólio aqui na
   Workana" — NUNCA cole link externo.
2) REDUÇÃO DE RISCO pro cliente (escolha o que couber): entrega em etapas/marcos
   com aprovação a cada uma; "você só aprova e paga ao ver funcionando"; ou um
   primeiro marco pequeno como teste. Tirar o risco do cliente vale mais que nota.
3) TOM confiante e específico. NUNCA diga que é iniciante, novo na plataforma ou
   que "está começando". Demonstre competência pelo plano e pela prova, não peça
   chance.
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
- "variacoes_abertura": 2-3 PRIMEIRAS LINHAS alternativas pra proposta, cada uma
  com um ângulo diferente (ex.: uma direta-ao-problema, uma com prova/resultado,
  uma com pergunta). É pra você testar qual converte mais (A/B). Curtas.

REGRAS (inegociáveis):
- ANTI-MENTIRA: use SOMENTE experiência/projetos/skills que ESTÃO no perfil.
  Reorganize a verdade, nunca invente. Se o perfil não cobre algo que o projeto
  pede, não finja que cobre.
- NÚMEROS SÃO SAGRADOS: NUNCA invente métricas, percentuais ou estatísticas
  ("taxa de sucesso de 90%", "redução de 40%", "3x mais rápido", "+200 clientes",
  "milhares de usuários"). Só use um número se ele estiver LITERALMENTE no perfil.
  Sem número medido, descreva o impacto QUALITATIVAMENTE ("gerava textos
  utilizáveis e acelerou a criação de campanhas") — jamais crave um percentual só
  pra impressionar. Um número fabricado que o cliente cobra depois destrói a
  confiança e a avaliação.
- PROVA OBRIGATÓRIA: inclua SEMPRE pelo menos 1 prova concreta — um resultado
  REAL de um projeto do perfil no formato problema → o que você fez → impacto.
  Adjetivo ("robusto", "escalável", "experiente") NÃO é prova; resultado é. O
  impacto pode ser qualitativo — NÃO precisa (nem pode) inventar número pra ele.
- PRAZO: deixe o prazo explícito no texto.
- Não force contato fora da plataforma (a Workana penaliza).
- NUNCA inclua no texto da proposta: e-mail, telefone, WhatsApp, ou links
  externos (GitHub, site, portfólio, LinkedIn). A Workana filtra/penaliza
  contato e links nas propostas e no chat antes do contrato. Para citar prova,
  DESCREVA o resultado (problema→solução→impacto) ou remeta ao "meu perfil/
  portfólio aqui na Workana" — sem colar URL.
- Não invente preço/valor — quem precifica é outro módulo.
- Português brasileiro, primeira pessoa, sem clichê de "sou apaixonado por...".
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt(
    descricao_projeto: str,
    perfil: PerfilMestreResponse,
    *,
    titulo: str | None = None,
    analise: dict | None = None,
    instrucoes_extra: str | None = None,
    cold_start: bool = False,
    texto_atual: str | None = None,
    correcoes: list | None = None,
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

    bloco_revisao = ""
    if texto_atual:
        pontos = "\n".join(f"- {c}" for c in (correcoes or [])) or "- (geral)"
        bloco_revisao = (
            "MODO REVISÃO: já existe um rascunho desta proposta. REESCREVA-O "
            "corrigindo EXATAMENTE os pontos abaixo, preservando o que já está "
            "bom. NÃO inclua contato/link no texto.\n\n"
            f"PONTOS A CORRIGIR:\n{pontos}\n\n"
            f"RASCUNHO ATUAL:\n{texto_atual}"
        )

    bloco_projeto = "\n".join(
        cab + ["", "DESCRIÇÃO DO PROJETO (texto colado):", descricao_projeto]
    )

    secoes = [INSTRUCOES.strip()]
    if cold_start:
        secoes.append(COLD_START.strip())
    secoes += [perfil_para_texto(perfil), bloco_projeto]
    if bloco_analise:
        secoes.append(bloco_analise)
    if bloco_revisao:
        secoes.append(bloco_revisao)
    if bloco_extra:
        secoes.append(bloco_extra)
    secoes += ["FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):", OUTPUT_SCHEMA.strip()]
    return "\n\n".join(secoes)
