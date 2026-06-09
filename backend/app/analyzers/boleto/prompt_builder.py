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
- Números sem separador de milhar e com ponto decimal (1107.52, não 1.107,52).
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt() -> str:
    return "\n\n".join([
        INSTRUCOES.strip(),
        "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):",
        OUTPUT_SCHEMA.strip(),
    ])
