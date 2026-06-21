"""Proposta: CRUD, mudança de status (com carimbo + crédito ao cliente) e as
fases de IA (redator/seletor, correção e negociador)."""
from __future__ import annotations

import json
from datetime import UTC, datetime

from app.analyzers.freela.negociador.parser import parse_resposta as parse_negociacao
from app.analyzers.freela.negociador.prompt_builder import (
    construir_prompt as construir_prompt_negociacao,
)
from app.analyzers.freela.redator.parser import parse_resposta as parse_redacao
from app.analyzers.freela.redator.prompt_builder import (
    construir_prompt as construir_prompt_redacao,
)
from app.api.schemas.freela import (
    NegociarRequest,
    NegociarResponse,
    PropostaCreate,
    PropostaResponse,
    PropostaStatusUpdate,
    PropostaUpdate,
    RedigirRequest,
    RedigirResponse,
)
from app.api.services.pessoal.perfil_service import get_perfil
from app.db.models.pessoal.freela.proposta import STATUS_PROPOSTA
from app.db.models.pipeline_event import PipelineEvent
from app.db.session import get_session
from app.repositories.pessoal.freela_repository import FreelaRepository

from ._base import FreelaError, _chamar_llm, _proposta_to_resp, _uuid

# Transições válidas que carimbam um timestamp na proposta.
_CARIMBO = {
    "enviada": "enviada_em",
    "respondida": "data_resposta",
    "fechada": "data_fechamento",
}
# As faixas de comissão são em US$, mas você cota em R$. Ao fechar, convertemos
# o líquido pra US$ por esta taxa (sobrescrevível em config_comissao.usd_brl).
_USD_BRL_PADRAO = 5.20


async def criar_proposta(payload: PropostaCreate) -> PropostaResponse:
    dados = payload.model_dump()
    projeto_id = _uuid(dados.pop("projeto_id"), "projeto_id")
    async with get_session() as session:
        repo = FreelaRepository(session)
        if await repo.get_projeto(projeto_id) is None:
            raise FreelaError("Projeto não encontrado.")
        dados["projeto_id"] = projeto_id
        proposta = await repo.create_proposta(dados)
        return _proposta_to_resp(proposta)


async def get_proposta(proposta_id: str) -> PropostaResponse:
    async with get_session() as session:
        proposta = await FreelaRepository(session).get_proposta(_uuid(proposta_id))
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        return _proposta_to_resp(proposta)


async def atualizar_proposta(proposta_id: str, payload: PropostaUpdate) -> PropostaResponse:
    dados = dict(payload.model_dump(exclude_unset=True))
    async with get_session() as session:
        proposta = await FreelaRepository(session).update_proposta(_uuid(proposta_id), dados)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        return _proposta_to_resp(proposta)


async def mudar_status(proposta_id: str, payload: PropostaStatusUpdate) -> PropostaResponse:
    novo = payload.status
    if novo not in STATUS_PROPOSTA:
        raise FreelaError(
            f"Status inválido: {novo!r}. Use um de: {', '.join(STATUS_PROPOSTA)}."
        )
    pid = _uuid(proposta_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        proposta = await repo.get_proposta(pid)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")

        anterior = proposta.status
        dados: dict = {"status": novo}
        # Carimba o timestamp da transição se ainda não tiver.
        campo = _CARIMBO.get(novo)
        if campo and getattr(proposta, campo) is None:
            dados[campo] = datetime.now(UTC)
        if novo == "perdida":
            dados["motivo_perda"] = payload.motivo_perda

        # Cliente recorrente vale ouro: ao FECHAR pela 1ª vez, soma o líquido
        # (convertido pra US$) ao acumulado do cliente → a comissão cai de faixa
        # sozinha e o precificador fica correto sem você lembrar.
        creditou_usd = 0.0
        if (
            novo == "fechada"
            and proposta.data_fechamento is None  # 1ª vez que fecha (não duplica)
            and proposta.valor_liquido_estimado
        ):
            projeto = await repo.get_projeto(proposta.projeto_id)
            if projeto and projeto.cliente_id:
                cliente = await repo.get_cliente(projeto.cliente_id)
                if cliente:
                    taxa = _USD_BRL_PADRAO
                    if projeto.plataforma_id:
                        plat = await repo.get_plataforma(projeto.plataforma_id)
                        if plat and plat.config_comissao:
                            taxa = float(plat.config_comissao.get("usd_brl", taxa))
                    creditou_usd = round(float(proposta.valor_liquido_estimado) / taxa, 2)
                    await repo.update_cliente(
                        cliente.id,
                        {"ja_me_pagou_usd": float(cliente.ja_me_pagou_usd) + creditou_usd},
                    )

        proposta = await repo.update_proposta(pid, dados)
        # Auditoria: reusa a tabela de eventos (pipeline_events).
        detalhe = json.dumps(
            {
                "proposta_id": proposta_id,
                "de": anterior,
                "para": novo,
                **({"creditou_usd": creditou_usd} if creditou_usd else {}),
            },
            ensure_ascii=False,
        )
        session.add(PipelineEvent(evento=f"freela_proposta_{novo}", detalhe=detalhe))
        await session.commit()
        return _proposta_to_resp(proposta)


async def deletar_proposta(proposta_id: str) -> None:
    async with get_session() as session:
        ok = await FreelaRepository(session).delete_proposta(_uuid(proposta_id))
        if not ok:
            raise FreelaError("Proposta não encontrada.")


async def listar_propostas_do_projeto(projeto_id: str) -> list[PropostaResponse]:
    async with get_session() as session:
        linhas = await FreelaRepository(session).listar_propostas_do_projeto(_uuid(projeto_id))
        return [_proposta_to_resp(p) for p in linhas]


# ── IA: redator + seletor (Fase 5) ───────────────────────────────

async def redigir_proposta(proposta_id: str, payload: RedigirRequest) -> RedigirResponse:
    perfil = await get_perfil()
    if perfil is None:
        raise FreelaError(
            "Cadastre seu Perfil Mestre antes de rascunhar — a proposta é "
            "ancorada nos seus projetos e habilidades."
        )

    pid = _uuid(proposta_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        proposta = await repo.get_proposta(pid)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        projeto = await repo.get_projeto(proposta.projeto_id)
        if projeto is None:
            raise FreelaError("Projeto da proposta não encontrado.")

        # Cold start: sem nenhuma proposta fechada, ainda não há reputação na
        # plataforma — o redator compensa isso (prova descrita + redução de risco).
        _, qtd_fechadas = await repo.soma_liquido_fechado()

        prompt = construir_prompt_redacao(
            projeto.descricao,
            perfil,
            titulo=projeto.titulo,
            analise=projeto.analise_json,
            instrucoes_extra=payload.instrucoes_extra,
            cold_start=qtd_fechadas == 0,
        )
        texto = _chamar_llm(prompt, operacao="redigir")

        redacao = parse_redacao(texto)
        if redacao is None:
            raise FreelaError("A IA não retornou um rascunho válido. Tente de novo.")

        # PARA no rascunho: preenche a proposta, nada é enviado.
        await repo.update_proposta(
            pid,
            {
                "texto_enviado": redacao.texto,
                "projetos_destacados": redacao.projetos_destacados,
                "habilidades_destacadas": redacao.habilidades_destacadas,
                "prazo_proposto": redacao.prazo_sugerido or proposta.prazo_proposto,
            },
        )

    return RedigirResponse(proposta_id=proposta_id, redacao=redacao)


async def corrigir_proposta(
    proposta_id: str, correcoes: list[str]
) -> RedigirResponse:
    """Reescreve a proposta corrigindo os pontos apontados pelo checklist."""
    perfil = await get_perfil()
    if perfil is None:
        raise FreelaError("Cadastre seu Perfil Mestre antes de corrigir a proposta.")

    pid = _uuid(proposta_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        proposta = await repo.get_proposta(pid)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        texto_atual = (proposta.texto_enviado or "").strip()
        if not texto_atual:
            raise FreelaError("Não há rascunho pra corrigir — gere a proposta antes.")
        projeto = await repo.get_projeto(proposta.projeto_id)
        if projeto is None:
            raise FreelaError("Projeto da proposta não encontrado.")

        _, qtd_fechadas = await repo.soma_liquido_fechado()
        prompt = construir_prompt_redacao(
            projeto.descricao,
            perfil,
            titulo=projeto.titulo,
            analise=projeto.analise_json,
            cold_start=qtd_fechadas == 0,
            texto_atual=texto_atual,
            correcoes=correcoes,
        )
        resposta = _chamar_llm(prompt, operacao="corrigir")
        redacao = parse_redacao(resposta)
        if redacao is None:
            raise FreelaError("A IA não retornou uma correção válida. Tente de novo.")

        await repo.update_proposta(
            pid,
            {
                "texto_enviado": redacao.texto,
                "projetos_destacados": redacao.projetos_destacados,
                "habilidades_destacadas": redacao.habilidades_destacadas,
                "prazo_proposto": redacao.prazo_sugerido or proposta.prazo_proposto,
            },
        )

    return RedigirResponse(proposta_id=proposta_id, redacao=redacao)


async def negociar_proposta(proposta_id: str, payload: NegociarRequest) -> NegociarResponse:
    if not payload.objecao.strip():
        raise FreelaError("Cole o que o cliente falou (a objeção).")

    pid = _uuid(proposta_id)
    async with get_session() as session:
        repo = FreelaRepository(session)
        proposta = await repo.get_proposta(pid)
        if proposta is None:
            raise FreelaError("Proposta não encontrada.")
        projeto = await repo.get_projeto(proposta.projeto_id)

    perfil = await get_perfil()  # opcional: dá o tom; funciona sem
    prompt = construir_prompt_negociacao(
        payload.objecao,
        perfil=perfil,
        titulo=projeto.titulo if projeto else None,
        valor_cotado=float(proposta.valor_cotado) if proposta.valor_cotado is not None else None,
        descricao_projeto=projeto.descricao if projeto else None,
    )
    texto = _chamar_llm(prompt, operacao="negociar")

    opcoes = parse_negociacao(texto)
    if not opcoes:
        raise FreelaError("A IA não retornou respostas válidas. Tente de novo.")

    return NegociarResponse(proposta_id=proposta_id, opcoes=opcoes)
