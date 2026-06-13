"""Prompt do importador de boleto (extração multimodal → JSON).

Pede ao LLM que leia um boleto (PDF/foto) e devolva beneficiário, vencimento,
valor total e a lista de verbas (subverbas), além de leituras de consumo quando
houver (caso do boleto de condomínio, que traz água/gás/luz).
"""
from __future__ import annotations

OUTPUT_SCHEMA = """
{
  "beneficiario": "<quem recebe (ex: Condomínio Edifício X / Lello)>",
  "vencimento": "<YYYY-MM-DD>",
  "valor_total": <número, ex: 1107.52>,
  "linha_digitavel": "<a linha digitável do boleto, só os números, ou null>",
  "multa_percentual": <número|null, ex: 2 para "multa de 2%">,
  "juros_mensal_percentual": <número|null, ex: 1 para "juros de 1% ao mês">,
  "desconto_valor": <número|null, valor do desconto por antecipação>,
  "desconto_ate": "<YYYY-MM-DD|null, data limite do desconto>",
  "verbas": [
    {"descricao": "<rubrica do boleto>", "valor": <número>},
    "..."
  ],
  "leituras": [
    {"tipo": "<agua|gas|luz>", "leitura_atual": <número|null>,
     "leitura_anterior": <número|null>, "consumo": <número|null>, "valor": <número|null>}
  ]
}
"""

INSTRUCOES = """
Você lê um BOLETO (pode ser PDF ou foto) e extrai os dados de forma estruturada.

REGRAS:
- "valor_total": o valor a pagar do boleto, como número (use ponto decimal).
- "verbas": cada rubrica/linha de cobrança do boleto, com sua descrição e valor.
  A SOMA das verbas deve ser igual ao valor_total. Se o boleto não detalha
  rubricas, devolva uma única verba igual ao total.
- "leituras": só quando o boleto traz medição de consumo (água/gás/luz),
  comum em condomínio. Caso contrário, devolva lista vazia.
- "vencimento": data no formato YYYY-MM-DD. Se não achar, use null.
- "linha_digitavel": a sequência numérica longa do boleto (a "linha digitável",
  ~47-48 dígitos), só os números — sem pontos, espaços ou traços. Se não der
  pra ler com confiança, use null (não invente).
- "multa_percentual" e "juros_mensal_percentual": leia as instruções de
  pagamento/encargos do boleto (ex.: "após o vencimento, multa de 2% e juros de
  1% ao mês" / "mora de 0,033% ao dia"). Devolva só o número do percentual
  (multa única → multa_percentual; juros mensais → juros_mensal_percentual). Se
  o boleto informar juros AO DIA, multiplique por 30 pra virar mensal. Se não
  houver, use null. NÃO invente valores.
- "desconto_valor"/"desconto_ate": se o boleto oferecer desconto por pagamento
  antecipado (ex.: "desconto de R$10,00 até 05/06"), traga o valor e a data
  limite (YYYY-MM-DD). Sem desconto, use null.
- Números sem separador de milhar e com ponto decimal (1107.52, não 1.107,52).
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt() -> str:
    return "\n\n".join([
        INSTRUCOES.strip(),
        "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):",
        OUTPUT_SCHEMA.strip(),
    ])
