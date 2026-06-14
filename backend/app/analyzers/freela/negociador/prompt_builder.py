"""Prompt do assistente de negociação (freela / Workana).

O cliente fez uma objeção (geralmente preço). Gera 2-3 respostas com
estratégias DIFERENTES — sempre defendendo o valor ou trocando escopo por
preço, nunca dando desconto seco nem soando desesperado. PARA aí: você escolhe,
edita e responde na mão dentro da plataforma.
"""
from __future__ import annotations

from typing import Optional

from app.analyzers._perfil_texto import perfil_para_texto
from app.api.schemas.pessoal import PerfilMestreResponse


OUTPUT_SCHEMA = """
{
  "opcoes": [
    "<resposta 1 — DEFENDE o valor: reforça o que ele leva (resultado/risco evitado), mantém o preço>",
    "<resposta 2 — TROCA escopo por preço: oferece uma versão menor/faseada pelo valor que ele topa, sem baixar seu valor-hora>",
    "<resposta 3 — pequena CONCESSÃO ancorada: condiciona o desconto a algo (prazo maior, pagamento adiantado, depoimento/portfólio)>"
  ]
}
"""

INSTRUCOES = """
Você é um freelancer experiente NEGOCIANDO uma proposta. O cliente fez uma
objeção (quase sempre de preço). Gere respostas curtas, profissionais e no tom
do freelancer.

PRINCÍPIOS:
- NUNCA dê desconto seco ("ok, faço por menos"). Isso destrói margem e sinaliza
  que o preço era inflado.
- Defenda o VALOR (o que o cliente leva: resultado, tempo, risco evitado) OU
  troque ESCOPO por preço (entrega menor/faseada) OU faça concessão CONDICIONADA
  (prazo, antecipação, depoimento).
- Tom firme e cordial, sem desespero, sem submissão. Primeira pessoa.
- Não force contato/pagamento fora da plataforma.
- Cada opção é uma ESTRATÉGIA diferente (não três jeitos de dizer o mesmo).
- Português brasileiro. Responda APENAS com JSON. Sem markdown.
"""


def construir_prompt(
    objecao: str,
    *,
    perfil: Optional[PerfilMestreResponse] = None,
    titulo: Optional[str] = None,
    valor_cotado: Optional[float] = None,
    descricao_projeto: Optional[str] = None,
) -> str:
    ctx = []
    if titulo:
        ctx.append(f"Projeto: {titulo}")
    if valor_cotado:
        ctx.append(f"Valor que você cotou: R$ {valor_cotado:.2f}")
    if descricao_projeto:
        ctx.append(f"Sobre o projeto: {descricao_projeto[:600]}")
    ctx.append(f'Objeção do cliente: "{objecao}"')

    secoes = [INSTRUCOES.strip()]
    if perfil is not None:
        secoes.append(perfil_para_texto(perfil))
    secoes.append("\n".join(ctx))
    secoes += ["FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):", OUTPUT_SCHEMA.strip()]
    return "\n\n".join(secoes)
