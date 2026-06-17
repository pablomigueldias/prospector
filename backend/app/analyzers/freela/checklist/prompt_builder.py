"""Prompt do Checklist anti-genérico (gate de qualidade da proposta).

No rascunho PRONTO, confere se a proposta foge do copia-cola: cita detalhe
real do projeto, propõe plano, tem prazo, traz prova e evita clichê. Devolve
um score, um selo e o que faltou. A conformidade (contato/link) é checada
fora daqui, de forma determinística.
"""
from __future__ import annotations

OUTPUT_SCHEMA = """
{
  "itens": [
    {"criterio": "Cita um detalhe REAL e específico do projeto", "ok": true/false, "nota": "<1 frase>"},
    {"criterio": "Propõe um plano em passos (não só preço)", "ok": true/false, "nota": "<1 frase>"},
    {"criterio": "Tem prazo claro", "ok": true/false, "nota": "<1 frase>"},
    {"criterio": "Traz prova/resultado concreto", "ok": true/false, "nota": "<1 frase>"},
    {"criterio": "Foge de clichê genérico", "ok": true/false, "nota": "<1 frase>"}
  ],
  "score": <inteiro 0-100>,
  "sugestoes": ["<melhoria objetiva e curta>", "..."]
}
"""

INSTRUCOES = """
Você é um revisor crítico de propostas de freelancer (estilo Workana). Recebe a
DESCRIÇÃO DO PROJETO e o TEXTO DA PROPOSTA já escrita. Avalie SE a proposta foge
do copia-cola que os clientes ignoram. Confira EXATAMENTE estes 5 critérios:

1. Cita um detalhe REAL e específico do projeto (prova que leu — não algo que
   serviria pra qualquer projeto).
2. Propõe um PLANO em passos do que vai fazer (não só um preço/promessa vaga).
3. Tem um PRAZO claro.
4. Traz PROVA/resultado concreto (algo que já fez, descrito) — não só adjetivos.
5. FOGE DE CLICHÊ ("sou apaixonado por...", "tenho ampla experiência", "melhor
   custo-benefício", "entrego com qualidade") — linguagem específica, não genérica.

Para cada critério, "ok" (true/false) e uma "nota" curta dizendo por quê.
"score": 0-100 ponderado pela força geral (cada critério ~20 pontos; desconte
mais se a proposta inteira soa genérica).
"sugestoes": 1-3 melhorias objetivas e acionáveis (o que reescrever), só se houver
o que melhorar.

REGRAS:
- Seja exigente: proposta é escassa, nenhuma deve sair fraca.
- Não reescreva a proposta aqui — só avalie e aponte.
- Português brasileiro. Responda APENAS com JSON. Sem markdown.
"""


def construir_prompt(
    texto_proposta: str, *, descricao_projeto: str | None = None,
    titulo: str | None = None,
) -> str:
    bloco = []
    if titulo:
        bloco.append(f"Título do projeto: {titulo}")
    if descricao_projeto:
        bloco.append("DESCRIÇÃO DO PROJETO:\n" + descricao_projeto)
    bloco.append("TEXTO DA PROPOSTA (avalie este):\n" + texto_proposta)

    return "\n\n".join([
        INSTRUCOES.strip(),
        "\n\n".join(bloco),
        "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):",
        OUTPUT_SCHEMA.strip(),
    ])
