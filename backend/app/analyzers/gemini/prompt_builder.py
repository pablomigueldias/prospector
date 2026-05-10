from typing import Dict, List, Optional

from app.models.lead import Lead


OUTPUT_SCHEMA = """
{
  "score": <inteiro 0-100>,
  "score_justificativa": "<frase curta explicando o score>",
  "porte_estimado": "<descrição livre, ex: 'Pequena empresa familiar'>",
  "perfil_negocio": "<2-3 frases descrevendo o que a empresa faz e seu posicionamento>",
  "dores_provaveis": [
    {
      "dor": "<descrição da dor>",
      "evidencia": "<dado direto observado OU 'suposição' se baseado em padrão do setor>"
    }
  ],
  "ganchos_venda": [
    {
      "produto_servico": "<o que ofertar>",
      "porque_faz_sentido": "<por que essa empresa especificamente precisaria>"
    }
  ],
  "perguntas_call": [
    "<pergunta 1>",
    "<pergunta 2>",
    "<pergunta 3>"
  ],
  "alertas": [
    "<algo que vale atenção, ex: situação cadastral irregular, site quebrado, etc.>"
  ],
  "resumo_executivo": "<2-4 linhas que resumem a oportunidade pra colar numa apresentação>"
}
"""


def _formatar_capital(capital: Optional[float]) -> str:
    if capital is None:
        return "(não informado)"
    if capital >= 1_000_000:
        return f"R$ {capital / 1_000_000:.1f}M"
    if capital >= 1_000:
        return f"R$ {capital / 1_000:.0f}k"
    return f"R$ {capital:.2f}"


def _bloco_empresa(lead: Lead) -> str:
    e = lead.empresa
    socios_str = (
        ", ".join(f"{s.nome} ({s.qualificacao or 'sócio'})" for s in e.socios)
        if e.socios else "(não informados)"
    )
    return f"""[EMPRESA]
- Nome: {e.nome}
- Razão Social: {e.razao_social or '(não informada)'}
- CNPJ: {e.cnpj or '(não informado)'}
- Capital Social: {_formatar_capital(e.capital_social)}
- Setor (estimado): {e.setor or '(não classificado)'}
- Tamanho (estimado): {e.tamanho or '(não classificado)'}
- Localização: {e.cidade or '?'}/{e.estado or '?'}
- Endereço: {e.local or '(não informado)'}
- Sócios: {socios_str}"""


def _bloco_presenca_digital(lead: Lead) -> str:
    e = lead.empresa
    site = e.site or "(não tem ou não informado)"
    instagram = e.instagram or "(não tem ou não informado)"
    facebook = e.facebook or "(não tem ou não informado)"
    return f"""[PRESENÇA DIGITAL]
- Site: {site}
- Instagram: {instagram}
- Facebook: {facebook}"""


def _bloco_contatos(lead: Lead) -> str:
    if not lead.contatos:
        return "[CONTATOS]\n- (Nenhum contato identificado)"

    linhas = ["[CONTATOS]"]
    for c in lead.contatos:
        partes = [f"- {c.nome}"]
        if c.cargo:
            partes.append(f"({c.cargo})")
        if c.decisor:
            partes.append("[DECISOR]")
        linhas.append(" ".join(partes))
        if c.email:
            linhas.append(f"   {c.email}")
        if c.whatsapp:
            linhas.append(f"   {c.whatsapp}")
        if c.telefone:
            linhas.append(f"   {c.telefone}")
        if c.linkedin:
            linhas.append(f"   {c.linkedin}")
    return "\n".join(linhas)


def _bloco_observacoes(lead: Lead) -> str:
    if not lead.empresa.notas:
        return ""
    return f"[OBSERVAÇÕES DOS COLETORES]\n{lead.empresa.notas}"


INSTRUCOES = """
Você é um analista de pré-vendas B2B especializado em **transformação digital
e desenvolvimento de software sob medida**. A empresa que você assessora vende:
- Sites institucionais e e-commerce
- Sistemas web personalizados
- Automações de processo
- Integrações de sistemas

Seu trabalho: analisar uma empresa potencial e gerar uma análise crítica em
JSON, focada em descobrir oportunidades concretas de venda dos serviços acima.

REGRAS DE QUALIDADE — siga rigorosamente:

1. **Modo conservador**: marque cada dor/gancho como "evidência direta" (algo
   visível nos dados) ou "suposição" (extrapolação baseada em padrão do setor).

2. **Específico, não genérico**: nada de "talvez precisem de digitalização".
   Diga EXATAMENTE o quê: "loja sem e-commerce, perde vendas online".

3. **Score 0-100** baseado em:
   - 0-30: lead fraco (empresa muito pequena, situação cadastral ruim, sem dados)
   - 31-60: lead morno (potencial mas sinais mistos)
   - 61-80: lead bom (claros pontos a melhorar, porte compatível)
   - 81-100: lead quente (dores óbvias, decisor identificado, empresa saudável)

4. **Português brasileiro**, tom profissional mas direto. Sem jargão de venda
   tipo "alavancar sinergias".

5. **Máximo 3 dores e 3 ganchos** — qualidade, não quantidade.

6. **Perguntas pra call** que descubram fato, não que vendam (ex: "como vocês
   gerenciam pedidos hoje?", não "vocês querem um sistema de gestão?").

7. **Alertas**: avise se a empresa tem situação cadastral irregular, sócio
   único pode dificultar venda, site quebrado, etc.

Responda APENAS com o JSON. Sem texto antes ou depois. Sem markdown ```json.
"""


def construir_prompt(lead: Lead) -> str:
    blocos = [
        INSTRUCOES.strip(),
        "",
        "DADOS DA EMPRESA A ANALISAR:",
        "",
        _bloco_empresa(lead),
        "",
        _bloco_presenca_digital(lead),
        "",
        _bloco_contatos(lead),
    ]

    obs = _bloco_observacoes(lead)
    if obs:
        blocos.append("")
        blocos.append(obs)

    blocos.extend([
        "",
        "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON, sem markdown):",
        OUTPUT_SCHEMA.strip(),
    ])

    return "\n".join(blocos)
