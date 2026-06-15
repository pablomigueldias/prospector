"""Prompt do gerador de currículo sob medida pra uma vaga.

Pega o PERFIL MESTRE + a VAGA (e a análise/match, se houver) e produz um
currículo ADAPTADO àquela vaga: resumo que fala com a vaga, habilidades
priorizadas pelos requisitos, projetos mais relevantes na frente e experiências
viradas em realizações que conversam com o que a vaga pede.

REGRA ANTI-MENTIRA (igual à candidatura): reorganiza a verdade do perfil, NUNCA
inventa experiência/skill/resultado que não está lá. Dados factuais (nome,
contato, formação) NÃO saem daqui — o serviço injeta direto do perfil.
"""
from __future__ import annotations

from typing import Optional

from app.analyzers._perfil_texto import (
    blocos_curriculo_para_texto,
    perfil_para_texto,
)
from app.api.schemas.pessoal import PerfilMestreResponse


OUTPUT_SCHEMA = """
{
  "titulo": "<headline curta adaptada à vaga (ex.: 'Desenvolvedor Frontend')>",
  "resumo": "<2-4 frases de topo de currículo (seção SOBRE), escritas PRA ESTA vaga: o que você entrega que ela pede>",
  "competencias": [
    {
      "categoria": "<rótulo do grupo, ex.: 'Linguagens', 'Frameworks', 'Backend', 'Banco de Dados', 'Ferramentas', 'Integrações'>",
      "itens": ["<skills do perfil que caem nesse grupo>"]
    }
  ],
  "experiencias": [
    {
      "cargo": "<como está no perfil>",
      "empresa": "<como está no perfil>",
      "periodo": "<como está no perfil>",
      "bullets": ["<2-4 realizações em 1 linha cada, com verbo de ação, conectando o que você fez ao que a vaga pede — SÓ o que o perfil evidencia>"]
    }
  ],
  "projetos": [
    {
      "nome": "<nome EXATO do projeto como está no perfil>",
      "descricao": "<1-2 frases adaptadas à vaga: o que o projeto prova pra ela, espelhando termos da vaga>",
      "stack": ["<tecnologias do projeto relevantes pra vaga>"],
      "link": "<link do projeto SE houver no perfil, senão null>"
    }
  ]
}
"""

INSTRUCOES = """
Você é um especialista em currículos técnicos. Recebe o PERFIL MESTRE de um
candidato e uma VAGA. Produza um currículo ENXUTO e ADAPTADO àquela vaga:

- "titulo": headline curta que casa com o cargo da vaga.
- "resumo": 2-4 frases no topo (seção SOBRE), falando diretamente ao que a vaga
  procura, com os pontos mais fortes do candidato PRA ELA.
- "competencias": AGRUPE as skills do perfil em categorias com rótulo CURTO
  (1-2 palavras, ex.: Linguagens, Frameworks, Backend, Banco de Dados,
  Ferramentas, Integrações). Ponha na frente os grupos/itens que a vaga exige.
  Use só as categorias que fizerem sentido pro que existe no perfil — não force
  grupos vazios. Máx ~6 grupos.
- "experiencias": para cada experiência do perfil, escreva 2-4 bullets de
  realização (verbo de ação no início) que conectem o que a pessoa fez ao que a
  vaga pede. Use SÓ o que o perfil mostra.
- "projetos": escolha os 2-4 projetos do perfil MAIS relevantes pra esta vaga,
  com 1-2 frases focadas nela e a stack que importa. Ótimo pra reforçar
  palavras-chave e preencher o currículo quando a experiência formal é curta.
  Use o nome EXATO do perfil; só inclua link se ele existir no perfil.

OTIMIZAÇÃO ATS (o currículo vai pra um banco que ranqueia por palavra-chave):
- ESPELHE os termos EXATOS da vaga (tecnologias, ferramentas, cargo). Se a vaga
  diz "React.js", escreva "React.js", não "React". Evite sinônimos.
- Use a sigla/forma EXATA como a vaga usa (ex.: se a vaga diz "APIs REST", use
  "APIs REST"). Quando fizer sentido, traga a forma por extenso + sigla.
- Repita os termos mais críticos da vaga 2-3x de forma natural (resumo,
  competências e bullets). NUNCA crie uma seção "Palavras-chave" — ATS pune isso.
- Experiências em ordem CRONOLÓGICA REVERSA (mais recente primeiro).
- O "titulo" deve espelhar o cargo da vaga quando o perfil sustentar.

REGRAS (inegociáveis):
- ANTI-MENTIRA: só o que está no perfil. Reorganize/enfatize a verdade e espelhe
  os termos da vaga que o perfil sustenta — espelhar NÃO é inventar. Nunca crie
  cargo, empresa, número ou skill que não existe.
- Bullets curtos, concretos, sem encher linguiça. Português brasileiro.
- Responda APENAS com JSON. Sem markdown, sem texto antes ou depois.
"""


def construir_prompt(
    perfil: PerfilMestreResponse,
    descricao_vaga: str,
    *,
    titulo_vaga: Optional[str] = None,
    empresa: Optional[str] = None,
    analise_json: Optional[dict] = None,
    match_json: Optional[dict] = None,
) -> str:
    cab = []
    if titulo_vaga:
        cab.append(f"Cargo da vaga: {titulo_vaga}")
    if empresa:
        cab.append(f"Empresa: {empresa}")

    # Palavras-chave da vaga (motor de ranking do ATS): vêm da análise já feita.
    bloco_kw = ""
    if analise_json:
        grupos = [
            ("OBRIGATÓRIOS", analise_json.get("requisitos_obrigatorios") or []),
            ("Stack", analise_json.get("stack") or []),
            ("Desejáveis", analise_json.get("desejaveis") or []),
        ]
        partes = [f"{rot}: " + "; ".join(itens[:12]) for rot, itens in grupos if itens]
        if partes:
            bloco_kw = (
                "PALAVRAS-CHAVE DA VAGA (espelhe os termos EXATOS que o perfil "
                "sustentar, priorizando os obrigatórios):\n" + "\n".join(partes)
            )

    bloco_match = ""
    if match_json:
        tenho = match_json.get("tenho") or []
        destaques = match_json.get("destaques") or []
        partes = []
        if tenho:
            partes.append("Requisitos que o candidato JÁ atende: " + "; ".join(tenho[:8]))
        if destaques:
            partes.append("Pontos a destacar nesta vaga: " + "; ".join(destaques[:5]))
        if partes:
            bloco_match = "CRUZAMENTO VAGA×CANDIDATO (use pra priorizar):\n" + "\n".join(partes)

    bloco_vaga = "\n".join(cab + ["", "DESCRIÇÃO DA VAGA:", descricao_vaga])

    secoes = [INSTRUCOES.strip(), perfil_para_texto(perfil)]
    blocos = blocos_curriculo_para_texto(perfil)
    if blocos:
        secoes.append(blocos)
    secoes.append(bloco_vaga)
    if bloco_kw:
        secoes.append(bloco_kw)
    if bloco_match:
        secoes.append(bloco_match)
    secoes += ["FORMATO DE SAÍDA OBRIGATÓRIO (apenas JSON):", OUTPUT_SCHEMA.strip()]
    return "\n\n".join(secoes)
