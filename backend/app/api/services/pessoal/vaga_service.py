"""Service de Vagas — registro (Fase 1), análise+match (Fase 2/3) e
geração de candidatura (Fase 4). PARA no rascunho: nada aqui envia e-mail.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from app.analyzers.candidatura.parser import parse_resposta as parse_candidatura
from app.analyzers.candidatura.prompt_builder import (
    construir_prompt as construir_prompt_candidatura,
)
from app.analyzers.llm_provider import gerar_texto
from app.analyzers.vaga.parser import parse_resposta as parse_vaga
from app.analyzers.vaga.prompt_builder import (
    construir_prompt as construir_prompt_vaga,
)
from app.api.schemas.pessoal import (
    AnaliseVaga,
    AnalisarVagaResponse,
    CandidaturaEmailItem,
    GerarCandidaturaRequest,
    GerarCandidaturaResponse,
    MatchVaga,
    VagaCreate,
    VagaListItem,
    VagaListResponse,
    VagaResponse,
    VagaUpdate,
)
from app.api.services.pessoal.perfil_service import get_perfil
from app.db.models.pessoal.candidatura_email import CandidaturaEmail
from app.db.models.pessoal.vaga import Vaga
from app.db.session import get_session
from app.repositories.pessoal.vaga_repository import VagaRepository
from app.utils.logger import get_logger

logger = get_logger()


class VagaError(Exception):
    """Erro de negócio de Vagas — vira HTTP 400 no router."""


def _iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def _uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, AttributeError):
        raise VagaError(f"id de vaga inválido: {valor!r}")


def _to_response(v: Vaga) -> VagaResponse:
    return VagaResponse(
        id=str(v.id),
        titulo=v.titulo,
        empresa=v.empresa,
        link=v.link,
        fonte=v.fonte,
        contato_nome=v.contato_nome,
        contato_email=v.contato_email,
        localizacao=v.localizacao,
        modelo=v.modelo,
        senioridade=v.senioridade,
        descricao=v.descricao,
        notas=v.notas,
        status=v.status,
        analise_json=v.analise_json,        # pydantic coage dict→AnaliseVaga
        match_json=v.match_json,
        match_score=v.match_score,
        created_at=_iso(v.created_at),
        updated_at=_iso(v.updated_at),
    )


# ── CRUD ─────────────────────────────────────────────────────────

async def criar_vaga(payload: VagaCreate) -> VagaResponse:
    if not payload.titulo.strip():
        raise VagaError("A vaga precisa de um título.")
    if not payload.descricao.strip():
        raise VagaError("Cole a descrição da vaga.")

    async with get_session() as session:
        vaga = await VagaRepository(session).create(payload.model_dump())
        return _to_response(vaga)


async def listar_vagas(status: Optional[str] = None) -> VagaListResponse:
    async with get_session() as session:
        linhas = await VagaRepository(session).listar(status=status)
        items = [
            VagaListItem(
                id=str(v.id),
                titulo=v.titulo,
                empresa=v.empresa,
                status=v.status,
                modelo=v.modelo,
                senioridade=v.senioridade,
                match_score=v.match_score,
                tem_analise=v.analise_json is not None,
                qtd_rascunhos=qtd,
                created_at=_iso(v.created_at),
            )
            for v, qtd in linhas
        ]
    return VagaListResponse(items=items, total=len(items))


async def get_vaga(vaga_id: str) -> VagaResponse:
    async with get_session() as session:
        vaga = await VagaRepository(session).get(_uuid(vaga_id))
        if vaga is None:
            raise VagaError("Vaga não encontrada.")
        return _to_response(vaga)


async def atualizar_vaga(vaga_id: str, payload: VagaUpdate) -> VagaResponse:
    dados = payload.model_dump(exclude_unset=True)
    async with get_session() as session:
        vaga = await VagaRepository(session).update(_uuid(vaga_id), dados)
        if vaga is None:
            raise VagaError("Vaga não encontrada.")
        return _to_response(vaga)


async def deletar_vaga(vaga_id: str) -> bool:
    async with get_session() as session:
        ok = await VagaRepository(session).delete(_uuid(vaga_id))
        if not ok:
            raise VagaError("Vaga não encontrada.")
        return True


# ── IA: análise + match (Fase 2/3) ───────────────────────────────

async def analisar_vaga(vaga_id: str) -> AnalisarVagaResponse:
    perfil = await get_perfil()
    if perfil is None:
        raise VagaError(
            "Cadastre seu Perfil Mestre antes de analisar vagas — "
            "a análise cruza a vaga com quem você é."
        )

    async with get_session() as session:
        repo = VagaRepository(session)
        vaga = await repo.get(_uuid(vaga_id))
        if vaga is None:
            raise VagaError("Vaga não encontrada.")

        prompt = construir_prompt_vaga(
            vaga.descricao, perfil, titulo=vaga.titulo, empresa=vaga.empresa
        )
        texto = _chamar_llm(prompt, agente="vaga", operacao="analisar")

        resultado = parse_vaga(texto)
        if resultado is None:
            raise VagaError("A IA não retornou uma análise válida. Tente de novo.")
        analise, match = resultado

        await repo.salvar_analise(
            _uuid(vaga_id),
            analise.model_dump(mode="json"),
            match.model_dump(mode="json"),
            match.aderencia,
        )

    return AnalisarVagaResponse(
        analise=analise, match=match, match_score=match.aderencia
    )


# ── IA: geração de candidatura (Fase 4) ──────────────────────────

async def gerar_candidatura(
    vaga_id: str, payload: GerarCandidaturaRequest
) -> GerarCandidaturaResponse:
    perfil = await get_perfil()
    if perfil is None:
        raise VagaError(
            "Cadastre seu Perfil Mestre antes — sem ele a carta sai genérica."
        )

    async with get_session() as session:
        repo = VagaRepository(session)
        vaga = await repo.get(_uuid(vaga_id))
        if vaga is None:
            raise VagaError("Vaga não encontrada.")

        analise = AnaliseVaga(**vaga.analise_json) if vaga.analise_json else None
        match = MatchVaga(**vaga.match_json) if vaga.match_json else None

        prompt = construir_prompt_candidatura(
            perfil,
            titulo=vaga.titulo,
            empresa=vaga.empresa,
            analise=analise,
            match=match,
            gerar_carta=payload.gerar_carta,
            instrucoes_extra=payload.instrucoes_extra,
        )
        texto = _chamar_llm(prompt, agente="candidatura", operacao="gerar")

        resultado = parse_candidatura(texto)
        if resultado is None:
            raise VagaError("A IA não retornou um rascunho válido. Tente de novo.")

        # Persiste o rascunho — status nasce 'rascunho'. Envio é manual.
        contexto = {
            "match_score": vaga.match_score,
            "instrucoes_extra": payload.instrucoes_extra,
        }
        email_row = await repo.add_email({
            "vaga_id": vaga.id,
            "tipo": "email",
            "destinatario": vaga.contato_email,
            "assunto": resultado.email.assunto,
            "corpo": resultado.email.corpo,
            "tom": resultado.email.tom,
            "status": "rascunho",
            "variantes": [v.model_dump(mode="json") for v in resultado.variantes_email],
            "contexto": contexto,
        })

        if resultado.carta:
            await repo.add_email({
                "vaga_id": vaga.id,
                "tipo": "carta",
                "destinatario": vaga.contato_email,
                "corpo": resultado.carta.corpo,
                "tom": resultado.carta.tom,
                "status": "rascunho",
                "contexto": contexto,
            })

        resultado.rascunho_id = str(email_row.id)

    logger.info("Candidatura: rascunho gerado pra vaga %s", vaga_id)
    return resultado


async def listar_rascunhos(vaga_id: str) -> List[CandidaturaEmailItem]:
    async with get_session() as session:
        rows = await VagaRepository(session).listar_emails(_uuid(vaga_id))
        return [
            CandidaturaEmailItem(
                id=str(r.id),
                vaga_id=str(r.vaga_id),
                tipo=r.tipo,
                destinatario=r.destinatario,
                assunto=r.assunto,
                corpo=r.corpo,
                tom=r.tom,
                status=r.status,
                created_at=_iso(r.created_at),
            )
            for r in rows
        ]


# ── helper LLM ───────────────────────────────────────────────────

def _chamar_llm(prompt: str, *, agente: str, operacao: str) -> str:
    try:
        return gerar_texto(
            prompt, json_mode=True, agente=agente, operacao=operacao
        )
    except Exception as e:
        logger.error("%s: falha na LLM: %s", agente, e)
        raise VagaError(
            "Não consegui falar com o modelo de IA. "
            "Verifique a conexão/configuração e tente de novo."
        )
