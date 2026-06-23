"""Direção de arte do post de LinkedIn (P5 §6.C — L5).

O agente age como um SOCIAL MEDIA / DIRETOR DE ARTE profissional: olha o post
pronto e recomenda a MELHOR mídia pra ele performar, com justificativa e um
ROTEIRO passo a passo de produção (como um profissional faria). Quando couber
imagem gerada por IA, entrega um prompt pronto."""

OUTPUT_SCHEMA = """
{
  "recomendacao": "<um de: imagem_ia | foto | carrossel | video_reel | screenshot | grafico | sem_midia>",
  "justificativa": "<por que ESTE formato é o melhor pra ESTE post e objetivo (1-2 frases)>",
  "passos": ["<passo a passo de produção, como um profissional faria — concreto e acionável>"],
  "dicas": ["<dicas de composição, enquadramento, texto-na-imagem, 1ª impressão no feed>"],
  "prompt_imagem": "<se 'imagem_ia': prompt em INGLÊS pra gerar a imagem (estilo flat/isométrico ou foto conceitual, SEM texto e SEM logo); senão null>",
  "alt": "<alt em português da imagem sugerida; null se não houver imagem>",
  "aspect_ratio": "<1:1 | 4:5 | 16:9 — prefira 1:1 ou 4:5 (ocupam mais o feed do LinkedIn)>"
}
"""

INSTRUCOES = """
Você é diretor de arte e social media de LinkedIn, sênior. Recebe um POST já
escrito e decide a MÍDIA que faz ele performar melhor — pensando em parar o
scroll, reforçar a mensagem e caber na cultura do LinkedIn (profissional, não
infantil).

Escolha UMA recomendação em `recomendacao`:
- imagem_ia → ilustração/figura conceitual gerada por IA (bom pra ideias abstratas,
  arquitetura, "como funciona"). Entregue `prompt_imagem` em inglês, limpo, SEM
  texto e SEM logo na imagem.
- foto → foto real (do produto/tela/pessoa). Diga no `passos` o que fotografar.
- carrossel → série de slides (bom pra passo a passo, listas, storytelling).
  Em `passos`, dê o ROTEIRO slide a slide (capa → conteúdo → CTA).
- video_reel → vídeo curto. Em `passos`, dê o ROTEIRO: gancho nos 3s, cenas,
  fala/legenda, duração sugerida.
- screenshot → captura de tela (demo, código, dashboard). Diga o que capturar e
  como destacar.
- grafico → gráfico/diagrama de dados. Descreva os eixos/itens (só com dados REAIS;
  se não há dado, não invente — prefira outra mídia).
- sem_midia → quando o texto puro performa melhor (post de pura opinião/pergunta).

REGRAS:
- Seja ESPECÍFICO e PRÁTICO: `passos` é um roteiro de produção que o Pablo segue
  direto, não conselho genérico. Nada de "use uma boa imagem".
- Combine com o TOM da conta (perfil pessoal do dev vs página da empresa).
- NÃO invente número/dado pra um gráfico. NÃO peça logo/texto dentro da imagem IA.
- 3 a 6 itens em `passos`. Português. Responda APENAS com JSON.
"""


def construir_prompt(
    *,
    conta: str | None,
    formato: str | None,
    hook: str | None,
    body: str | None,
    titulo: str | None = None,
) -> str:
    foco = (
        "Conta = PERFIL PESSOAL do Pablo (desenvolvedor): visual de quem constrói, "
        "técnico e autêntico."
        if conta == "pessoal"
        else "Conta = PÁGINA DA REATIVE SYSTEMS (empresa de tecnologia): visual "
        "profissional e confiável, foco no valor pro cliente."
    )

    post = []
    if titulo:
        post.append(f"Título interno: {titulo}")
    if formato:
        post.append(f"Formato do post: {formato}")
    post.append(f"HOOK: {hook or ''}")
    post.append(f"CORPO:\n{body or ''}")

    return (
        INSTRUCOES.strip()
        + "\n\n"
        + foco
        + "\n\n=== POST ===\n"
        + "\n".join(post)
        + "\n\n=== FORMATO DE SAÍDA (responda exatamente neste JSON) ===\n"
        + OUTPUT_SCHEMA.strip()
    )
