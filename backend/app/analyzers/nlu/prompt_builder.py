"""Prompt do NLU: interpreta uma frase solta sobre dinheiro e devolve a
estrutura da transação. Recebe as contas e categorias do usuário pra escolher
a melhor correspondência (em vez de inventar)."""
from __future__ import annotations

from datetime import date
from typing import List

OUTPUT_SCHEMA = """
{
  "tipo": "<despesa|receita>",
  "valor": <número, ex: 50.00>,
  "descricao": "<curta, ex: 'mercado'>",
  "categoria": "<uma das CATEGORIAS abaixo, ou null>",
  "conta": "<uma das CONTAS abaixo, ou null>",
  "data": "<YYYY-MM-DD>"
}
"""

INSTRUCOES = """
Você interpreta uma frase em português sobre uma movimentação financeira e
extrai os campos. Exemplos:
- "gastei 50 no mercado hoje" → despesa, 50, mercado
- "abasteci 200 de gasolina" → despesa, 200, gasolina
- "salário da Sandra caiu 3200" → receita, 3200, salário

REGRAS:
- "tipo": despesa (saiu dinheiro) ou receita (entrou).
- "valor": número positivo, ponto decimal.
- "categoria" e "conta": escolha SOMENTE entre as listas fornecidas; se nada
  encaixar bem, use null. Não invente nomes fora das listas.
- "data": resolva expressões relativas ("hoje", "ontem") em relação à DATA DE
  REFERÊNCIA. Se a frase não cita data, use a data de referência.
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt(
    texto: str, *, contas: List[str], categorias: List[str], hoje: date
) -> str:
    return "\n\n".join([
        INSTRUCOES.strip(),
        f"DATA DE REFERÊNCIA (hoje): {hoje.isoformat()}",
        "CONTAS disponíveis: " + (", ".join(contas) if contas else "(nenhuma)"),
        "CATEGORIAS disponíveis: " + (", ".join(categorias) if categorias else "(nenhuma)"),
        f'FRASE DO USUÁRIO:\n"{texto}"',
        "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):",
        OUTPUT_SCHEMA.strip(),
    ])
