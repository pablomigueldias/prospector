"""Prompt do Analisador de Projeto (freela / Workana).

Recebe o TEXTO DO PROJETO (você cola) + o PERFIL MESTRE + sinais do cliente,
e devolve fit score, red flags e ganchos. O objetivo é PROTEGER PROPOSTA
ESCASSA: dizer onde vale gastar bala. Espelha o analisador de vaga.
"""
from __future__ import annotations

from app.analyzers._perfil_texto import perfil_para_texto
from app.api.schemas.pessoal import PerfilMestreResponse

OUTPUT_SCHEMA = """
{
  "fit_score": <inteiro 0-100: quão "a sua praia" é este projeto>,
  "confianca_analise": "<alta | media | baixa — quanto o TEXTO COLADO permite analisar com segurança (não é o fit): baixa se for curto/genérico/sem escopo>",
  "confianca_motivo": "<1 frase: o que falta no texto pra ter certeza (ex.: 'só 2 linhas, sem escopo nem stack') — vazio se a confiança for alta>",
  "recomendacao": "<vale | talvez | evite>",
  "risco": "<baixo | medio | alto — risco de golpe/dor de cabeça: alto se cliente sem pagamento verificado + pede contato fora + oferta boa demais + escopo vago>",
  "complexidade_tecnica": "<trivial | media | alta | incerta — quão DIFÍCIL é tecnicamente (não confundir com tempo): trivial=CRUD/landing, alta=arquitetura/integrações complexas/IA, incerta=não dá pra saber pelo texto>",
  "clareza_escopo": "<claro | parcial | vago — o cliente descreveu o que quer a ponto de cotar com segurança? vago = risco de scope creep>",
  "veredito": "<1 frase honesta: vale gastar uma proposta aqui? por quê?>",
  "requisitos": ["<o que o projeto realmente pede>", "..."],
  "stack": ["<tecnologia citada/implícita>", "..."],
  "tarefas": [{"nome": "<entrega concreta do escopo>", "horas": <inteiro de horas pra ESSA entrega>}, "..."],
  "perguntas_cliente": ["<dúvida que muda o preço/prazo e precisa ser esclarecida antes de cotar>", "..."],
  "skills_faltando": ["<skill/experiência que o projeto exige e que NÃO aparece clara no perfil do freela (gap)>", "..."],
  "red_flags": ["<risco: orçamento incompatível com escopo, cliente sem pagamento verificado, projeto MUITO concorrido, escopo vago, prazo irreal, pedido fora do seu núcleo>", "..."],
  "sinais_cliente": ["<sinal de qualidade do cliente: verificado, nº de projetos pagos, rating, recorrência>", "..."],
  "ganchos": ["<algo do SEU perfil que conversa com este projeto — projeto/skill a citar>", "..."],
  "estimativa": {
    "horas_estimadas": <inteiro de horas de trabalho realistas, ou null>,
    "prazo_dias": <inteiro de dias corridos pra entregar, ou null>,
    "valor_mercado_min": <inteiro R$: piso honesto de mercado BR, ou null>,
    "valor_mercado_max": <inteiro R$: teto honesto de mercado BR, ou null>,
    "valor_sugerido": <inteiro R$: quanto COTAR dado fit e concorrência, ou null>
  }
}
"""

INSTRUCOES = """
Você é um estrategista de propostas freelancer. Numa plataforma como a Workana,
PROPOSTA É RECURSO ESCASSO: o freelancer manda poucas por período. Seu trabalho
é dizer ONDE VALE GASTAR essa bala — não escrever a proposta.

Recebe o TEXTO DE UM PROJETO publicado por um cliente, sinais desse cliente e o
PERFIL MESTRE do freelancer. Produza:

- "fit_score" (0-100): quão alinhado o projeto está com o que o freelancer
  COMPROVA no perfil. Projeto fora do núcleo dele = score baixo, por mais
  atraente que pareça.
- "confianca_analise": quanto o TEXTO COLADO te deixa analisar com SEGURANÇA —
  NÃO é o fit. "baixa" quando o texto é curto, genérico ou sem escopo/stack (aí
  NÃO finja certeza: rebaixe fit/estimativa pro lado conservador e diga em
  "confianca_motivo" o que falta pra cravar). "media" quando dá pra ter ideia mas
  faltam detalhes. "alta" só quando o texto descreve escopo o bastante pra cotar.
- "recomendacao": "vale" (fit alto, sinais bons), "talvez" (vale só se o preço/
  cliente compensar) ou "evite" (fit baixo ou muitas red flags).
- "risco": "alto" se houver sinais de golpe/perda de tempo (cliente sem
  pagamento verificado, pedido de contato/pagamento fora da plataforma, oferta
  "boa demais", escopo vago demais pra cotar); "medio" se um desses; "baixo" se
  o cliente parece sólido.
- "complexidade_tecnica": o quão DIFÍCIL tecnicamente — separe de tempo. Um CRUD
  grande pode ser "trivial" e demorado; uma integração de pagamento pode ser
  "alta" e rápida. "incerta" quando o texto não deixa claro.
- "clareza_escopo": "claro" se dá pra cotar com segurança, "parcial" se faltam
  detalhes que mudam o preço, "vago" se é genérico demais (risco de scope creep).
- "veredito": uma frase direta pra decidir.
- "requisitos" e "stack": o que o projeto pede de fato.
- "tarefas": quebre o escopo nas ENTREGAS concretas (ex.: "autenticação",
  "CRUD de produtos", "integração de pagamento", "deploy") com horas realistas
  por entrega. A SOMA das horas deve bater, grosso modo, com
  "estimativa.horas_estimadas". Se o escopo for vago demais pra quebrar, devolva
  lista vazia. Acaba com o "número de horas mágico".
- "perguntas_cliente": o que está AMBÍGUO e muda preço/prazo (ex.: "tem design
  pronto?", "quantas telas?", "precisa de painel admin?"). São as perguntas que
  você faria antes de cravar a cotação. Vazio se o escopo já estiver claro.
- "skills_faltando": seja honesto — skills/experiências que o projeto EXIGE e que
  NÃO aparecem claras no perfil do freela (o gap). Use só o que o projeto pede de
  verdade; se ele cobre tudo, devolva lista vazia. (É o oposto de "ganchos".)
- "red_flags": seja CÉTICO. Sinalize orçamento incompatível com o escopo,
  cliente sem pagamento verificado, projeto muito concorrido (muitas propostas/
  interessados), escopo vago, prazo irreal, ou pedido fora do núcleo do freela.
- "sinais_cliente": o que dá pra inferir da qualidade do cliente.
- "ganchos": SOMENTE projetos/skills que ESTÃO no perfil e conversam com este
  projeto (pra depois a proposta citar). Nunca invente experiência.
- "estimativa": estime o ESFORÇO e o PREÇO JUSTO DE MERCADO no Brasil pra este
  escopo (contexto freelancer/Workana):
  • "horas_estimadas": horas de trabalho realistas pro escopo descrito.
  • "prazo_dias": prazo de entrega realista em dias corridos.
  • "valor_mercado_min"/"max": faixa HONESTA que esse trabalho vale no mercado BR
    — nem inflado, nem fundo de poço. Baseie no escopo, stack e senioridade.
  • "valor_sugerido": quanto COTAR (R$), perto/levemente acima do mercado,
    ajustando pela concorrência (muito concorrido → mais competitivo) e pelo fit.
  Inteiros em R$. Se o escopo for vago demais pra estimar, use null nos campos.

REGRAS:
- Seja honesto no score. Inflar não ajuda — gasta proposta à toa.
- "ganchos" baseados SÓ no perfil. Não invente.
- Português brasileiro.
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt(
    descricao_projeto: str,
    perfil: PerfilMestreResponse,
    *,
    titulo: str | None = None,
    faixa_orcamento: str | None = None,
    n_propostas: int | None = None,
    n_interessados: int | None = None,
    sinais_cliente: str | None = None,
) -> str:
    cab = []
    if titulo:
        cab.append(f"Título do projeto: {titulo}")
    if faixa_orcamento:
        cab.append(f"Orçamento informado: {faixa_orcamento}")
    if n_propostas is not None:
        cab.append(f"Propostas concorrentes: {n_propostas}")
    if n_interessados is not None:
        cab.append(f"Interessados: {n_interessados}")
    if sinais_cliente:
        cab.append(f"Sinais do cliente: {sinais_cliente}")

    bloco_projeto = "\n".join(
        cab + ["", "DESCRIÇÃO DO PROJETO (texto colado):", descricao_projeto]
    )

    return "\n\n".join([
        INSTRUCOES.strip(),
        perfil_para_texto(perfil),
        bloco_projeto,
        "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):",
        OUTPUT_SCHEMA.strip(),
    ])
