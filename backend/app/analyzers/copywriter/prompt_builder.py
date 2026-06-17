from app.api.schemas.copywriter import CopywriterRequest

# --------------------------------------------------------------------------
# Schemas de saída — um por canal
# --------------------------------------------------------------------------

OUTPUT_SCHEMA_EMAIL = """
{
  "email": {
    "assunto": "<linha de assunto, máx 60 caracteres, sem clickbait>",
    "corpo": "<corpo completo do e-mail, com quebras de linha reais>",
    "cta": "<a frase exata de call-to-action usada no corpo>",
    "tom": "<2-3 palavras descrevendo o tom>"
  },
  "variantes": [
    {
      "assunto": "<assunto alternativo>",
      "corpo": "<corpo alternativo com abordagem diferente>",
      "cta": "<cta alternativo>",
      "tom": "<tom da variante>"
    }
  ]
}
"""

# No WhatsApp não há assunto. Mantemos o campo "assunto" no JSON por
# compatibilidade com o schema Pydantic, mas instruímos a deixá-lo vazio.
OUTPUT_SCHEMA_WHATSAPP = """
{
  "email": {
    "assunto": "",
    "corpo": "<mensagem de WhatsApp completa, curta, com quebras de linha>",
    "cta": "<a frase exata de call-to-action usada na mensagem>",
    "tom": "<2-3 palavras descrevendo o tom>"
  },
  "variantes": [
    {
      "assunto": "",
      "corpo": "<mensagem alternativa com abordagem diferente>",
      "cta": "<cta alternativo>",
      "tom": "<tom da variante>"
    }
  ]
}
"""


# --------------------------------------------------------------------------
# Instruções — um bloco por canal
# --------------------------------------------------------------------------

INSTRUCOES_EMAIL = """
Você é um especialista em copywriting e vendas B2B da Reative Systems,
uma empresa de desenvolvimento de software, automações e sites sob medida.

Sua tarefa: escrever um E-MAIL de abordagem que aumente a chance de
resposta positiva. O e-mail será lido por uma pessoa ocupada que recebe
dezenas de mensagens iguais por dia — o seu precisa parecer diferente.

REGRAS DE QUALIDADE — siga rigorosamente:

1. SOA HUMANO. Escreva como uma pessoa real escreveria. Sem frases de
   manual de vendas ("espero que esta mensagem o encontre bem",
   "venho por meio desta"). Comece direto e específico.

2. PERSONALIZE DE VERDADE. Use o nome, o cargo e principalmente o
   SEGMENTO da empresa. Cite a dor específica do nicho.

3. VALOR ANTES DE VENDER. Os dois primeiros parágrafos devem mostrar
   que você entende o problema do cliente. Só depois apresente o serviço.

4. CURTO. Máximo 150 palavras no corpo.

5. UM CTA SÓ, claro e de baixo atrito. Prefira "vale uma conversa de
   15 minutos esta semana?" a "agende uma reunião".

6. SEM EXAGERO. Nada de "revolucionário", "melhor do mercado".

7. PORTUGUÊS BRASILEIRO, tom profissional mas caloroso.

8. GERE 1 e-mail principal + 2 variantes com ângulos diferentes.

ESTRUTURA DO CORPO:
1. Abertura personalizada
2. Conexão com o problema ou oportunidade
3. Apresentação enxuta da solução
4. Um diferencial concreto
5. CTA de baixo atrito
6. Encerramento profissional e curto

Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""

INSTRUCOES_WHATSAPP = """
Você é um especialista em copywriting e vendas B2B da Reative Systems,
uma empresa de desenvolvimento de software, automações e sites sob medida.

Sua tarefa: escrever uma MENSAGEM DE WHATSAPP de primeira abordagem.
Isto NÃO é um e-mail encurtado — é outro registro de escrita.

REGRAS DE QUALIDADE — siga rigorosamente:

1. MUITO CURTA. Máximo 60 palavras no corpo inteiro. A mensagem é lida
   na notificação do celular — se parecer um texto longo, é ignorada.

2. SEM ASSUNTO. WhatsApp não tem linha de assunto. O campo "assunto"
   do JSON deve ficar VAZIO ("").

3. TOM DE CONVERSA, não de carta. Pode usar primeira pessoa direta
   ("vi que...", "tenho uma ideia pra..."). Nada de "prezado",
   "venho por meio desta" ou assinatura formal.

4. ABERTURA QUE IDENTIFICA QUEM ESCREVE. A pessoa não sabe quem você é.
   Diga em poucas palavras quem é a Reative Systems logo no começo.

5. UMA frase de valor + UMA pergunta no fim. Só isso. A pergunta deve
   ser fácil de responder ("faz sentido te mostrar como?", "posso te
   mandar um exemplo rápido?").

6. NADA DE PARÁGRAFOS LONGOS. Frases curtas, no máximo 2 quebras de
   linha. Pode usar no máximo 1 emoji, e só se ficar natural — nunca
   force.

7. PORTUGUÊS BRASILEIRO, informal mas profissional. Sem gírias.

8. NÃO pareça uma mensagem em massa. Mencione algo específico do
   segmento ou da necessidade do cliente.

9. GERE 1 mensagem principal + 2 variantes com ângulos diferentes.

Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


# --------------------------------------------------------------------------
# Montagem
# --------------------------------------------------------------------------

def _bloco_contexto(req: CopywriterRequest) -> str:
    linhas = ["DADOS PARA A MENSAGEM:"]
    campos = {
        "Empresa alvo": req.empresa,
        "Segmento": req.segmento,
        "Nome do contato": req.nome_contato,
        "Cargo": req.cargo,
        "Tipo de abordagem": req.tipo,
        "Necessidade identificada": req.necessidade,
        "Serviço oferecido": req.servico,
        "Diferenciais da Reative Systems": req.diferenciais,
    }
    for rotulo, valor in campos.items():
        linhas.append(f"- {rotulo}: {valor or '(não informado)'}")

    if req.contexto_extra:
        linhas.append("")
        linhas.append("CONTEXTO ADICIONAL (ex: descrição de vaga/projeto):")
        linhas.append(req.contexto_extra)

    return "\n".join(linhas)


def construir_prompt(req: CopywriterRequest) -> str:
    """Monta o prompt, escolhendo instruções e schema conforme o canal."""
    canal = (getattr(req, "canal", "email") or "email").lower()

    if canal == "whatsapp":
        instrucoes = INSTRUCOES_WHATSAPP
        schema = OUTPUT_SCHEMA_WHATSAPP
        rotulo_saida = "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON, mensagem de WhatsApp):"
    else:
        instrucoes = INSTRUCOES_EMAIL
        schema = OUTPUT_SCHEMA_EMAIL
        rotulo_saida = "FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):"

    return "\n\n".join([
        instrucoes.strip(),
        _bloco_contexto(req),
        rotulo_saida,
        schema.strip(),
    ])
