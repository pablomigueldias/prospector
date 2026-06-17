"""Gate anti-genérico: pontua o rascunho, mais scans determinísticos de
conformidade Workana (contato/link) e anti-mentira (número fora do perfil)."""
from __future__ import annotations

import re
from typing import Optional

from app.analyzers._perfil_texto import perfil_para_texto
from app.analyzers.freela.checklist.parser import parse_resposta as parse_checklist
from app.analyzers.freela.checklist.prompt_builder import (
    construir_prompt as construir_prompt_checklist,
)
from app.api.schemas.freela import ChecklistItem, ChecklistResponse
from app.api.services.pessoal.perfil_service import get_perfil
from app.db.session import get_session
from app.repositories.pessoal.freela_repository import FreelaRepository

from ._base import FreelaError, _chamar_llm, _uuid

# Conformidade Workana: contato/link no texto da proposta é filtrado/penalizado.
# CUIDADO: só pega CONTATO real, não menção ao tema. Ex.: "sistema para WhatsApp"
# é o assunto do projeto, NÃO o seu contato — não pode flagar.
_RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_RE_URL = re.compile(r"(https?://\S+|\bwww\.\S+|\b[\w-]+\.(?:com|net|io|dev|me|br)\b\S*)", re.I)
# telefone só quando tem cara de número de contato (DDD + 8/9 dígitos).
_RE_TEL = re.compile(r"(?:\+?55[\s-]*)?\(?\d{2}\)?[\s-]*9?\d{4}[\s-]?\d{4}")
# mensageria só por LINK explícito de contato (wa.me/t.me), não pela palavra solta.
_RE_ZAP = re.compile(r"\b(?:wa\.me|t\.me)/\S+", re.I)


def _scan_conformidade(texto: str) -> Optional[str]:
    """Acha CONTATO/link no texto da proposta (regra dura da Workana). None se limpo."""
    achados = []
    if _RE_EMAIL.search(texto):
        achados.append("e-mail")
    # tira e-mails antes de procurar URL (o domínio do e-mail não é "link").
    sem_email = _RE_EMAIL.sub(" ", texto)
    if _RE_TEL.search(sem_email):
        achados.append("telefone")
    if _RE_ZAP.search(texto) or _RE_URL.search(sem_email):
        achados.append("link externo")
    if not achados:
        return None
    return (
        "A proposta contém " + ", ".join(achados) + ". A Workana filtra/penaliza "
        "contato e link no texto antes do contrato — remova e remeta ao seu "
        "perfil/portfólio aqui na Workana."
    )


# Métrica "impressiva" inventada: a IA às vezes crava % / "Nx" que NÃO está no
# perfil (ex.: "90% de sucesso", "redução de 40%"). Pegamos números do texto que
# não aparecem no perfil pra alertar (anti-mentira determinístico). 100% é
# retórico ("100% focado") → ignorado pra reduzir falso-positivo.
_RE_METRICA = re.compile(r"\d{1,3}\s*%|\b\d+\s*x\b", re.I)


def _scan_metricas_inventadas(texto: str, perfil_texto: str) -> Optional[str]:
    """Acha número/percentual no texto que não está no perfil. None se limpo."""
    achados = _RE_METRICA.findall(texto)
    if not achados:
        return None
    perfil_digitos = set(re.findall(r"\d+", perfil_texto))
    suspeitos: list[str] = []
    for a in achados:
        nums = re.findall(r"\d+", a)
        if not nums or nums[0] in perfil_digitos:
            continue
        if a.rstrip().endswith("%") and nums[0] == "100":
            continue  # "100%" costuma ser retórico, não métrica fabricada
        token = a.strip().replace(" ", "")
        if token not in suspeitos:
            suspeitos.append(token)
    if not suspeitos:
        return None
    return (
        "Número(s) que NÃO encontrei no seu perfil: " + ", ".join(suspeitos) + ". "
        "A IA pode ter inventado — confirme que é real ou troque por descrição "
        "qualitativa (problema→solução→impacto, sem percentual fabricado)."
    )


def _selo(score: int) -> str:
    if score >= 80:
        return "pronta"
    if score >= 50:
        return "ajustar"
    return "fraca"


async def avaliar_proposta(proposta_id: str) -> ChecklistResponse:
    """Gate anti-genérico: pontua o rascunho e aponta o que falta antes de enviar."""
    pid = _uuid(proposta_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        proposta = await repo.get_proposta(pid)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        projeto = await repo.get_projeto(proposta.projeto_id)

    texto = (proposta.texto_enviado or "").strip()
    if not texto:
        raise FreelaError("Rascunhe a proposta antes de conferir (texto vazio).")

    prompt = construir_prompt_checklist(
        texto,
        descricao_projeto=projeto.descricao if projeto else None,
        titulo=projeto.titulo if projeto else None,
    )
    resposta = _chamar_llm(prompt, operacao="checklist")
    resultado = parse_checklist(resposta)
    if resultado is None:
        raise FreelaError("A IA não retornou uma avaliação válida. Tente de novo.")

    resultado.proposta_id = proposta_id

    # Conformidade Workana (determinística): contato/link no texto é penalizado.
    alerta = _scan_conformidade(texto)
    if alerta:
        resultado.alerta_conformidade = alerta
        resultado.itens.append(
            ChecklistItem(
                criterio="Sem contato/link externo (regra da Workana)",
                ok=False,
                nota="Encontrei contato ou link no texto.",
            )
        )
        # Conformidade fura tudo: limita o selo enquanto não corrigir.
        resultado.score = min(resultado.score, 49)

    # Anti-mentira determinístico: número/percentual no texto que não está no
    # perfil cheira a invenção da IA. Não derruba pra "fraca" (pode ser falso-
    # positivo), mas impede o selo "pronta" e avisa explicitamente.
    perfil = await get_perfil()
    if perfil is not None:
        alerta_num = _scan_metricas_inventadas(texto, perfil_para_texto(perfil))
        if alerta_num:
            resultado.itens.append(
                ChecklistItem(
                    criterio="Sem número inventado (anti-mentira)",
                    ok=False,
                    nota=alerta_num,
                )
            )
            resultado.sugestoes.append(alerta_num)
            resultado.score = min(resultado.score, 79)

    resultado.selo = _selo(resultado.score)
    return resultado
