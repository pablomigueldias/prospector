"""Prompt do Analisador de Projeto (freela / Workana).

Recebe o TEXTO DO PROJETO (você cola) + o PERFIL MESTRE + sinais do cliente,
e devolve fit score, red flags e ganchos. O objetivo é PROTEGER PROPOSTA
ESCASSA: dizer onde vale gastar bala. Espelha o analisador de vaga.
"""
from __future__ import annotations

from typing import Optional

from app.analyzers._perfil_texto import perfil_para_texto
from app.api.schemas.pessoal import PerfilMestreResponse


OUTPUT_SCHEMA = """
{
  "fit_score": <inteiro 0-100: quão "a sua praia" é este projeto>,
  "recomendacao": "<vale | talvez | evite>",
  "risco": "<baixo | medio | alto — risco de golpe/dor de cabeça: alto se cliente sem pagamento verificado + pede contato fora + oferta boa demais + escopo vago>",
  "veredito": "<1 frase honesta: vale gastar uma proposta aqui? por quê?>",
  "requisitos": ["<o que o projeto realmente pede>", "..."],
  "stack": ["<tecnologia citada/implícita>", "..."],
  "red_flags": ["<risco: orçamento incompatível com escopo, cliente sem pagamento verificado, projeto MUITO concorrido, escopo vago, prazo irreal, pedido fora do seu núcleo>", "..."],
  "sinais_cliente": ["<sinal de qualidade do cliente: verificado, nº de projetos pagos, rating, recorrência>", "..."],
  "ganchos": ["<algo do SEU perfil que conversa com este projeto — projeto/skill a citar>", "..."]
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
- "recomendacao": "vale" (fit alto, sinais bons), "talvez" (vale só se o preço/
  cliente compensar) ou "evite" (fit baixo ou muitas red flags).
- "risco": "alto" se houver sinais de golpe/perda de tempo (cliente sem
  pagamento verificado, pedido de contato/pagamento fora da plataforma, oferta
  "boa demais", escopo vago demais pra cotar); "medio" se um desses; "baixo" se
  o cliente parece sólido.
- "veredito": uma frase direta pra decidir.
- "requisitos" e "stack": o que o projeto pede de fato.
- "red_flags": seja CÉTICO. Sinalize orçamento incompatível com o escopo,
  cliente sem pagamento verificado, projeto muito concorrido (muitas propostas/
  interessados), escopo vago, prazo irreal, ou pedido fora do núcleo do freela.
- "sinais_cliente": o que dá pra inferir da qualidade do cliente.
- "ganchos": SOMENTE projetos/skills que ESTÃO no perfil e conversam com este
  projeto (pra depois a proposta citar). Nunca invente experiência.

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
    titulo: Optional[str] = None,
    faixa_orcamento: Optional[str] = None,
    n_propostas: Optional[int] = None,
    n_interessados: Optional[int] = None,
    sinais_cliente: Optional[str] = None,
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
