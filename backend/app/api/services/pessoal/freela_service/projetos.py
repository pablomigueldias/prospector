"""Projeto: CRUD (você cola o texto) + extração de campos por IA."""
from __future__ import annotations

from app.analyzers.freela.extrator.parser import parse_resposta as parse_extracao
from app.analyzers.freela.extrator.prompt_builder import (
    construir_prompt as construir_prompt_extracao,
)
from app.api.schemas.freela import (
    ExtrairProjetoResponse,
    ProjetoCreate,
    ProjetoListItem,
    ProjetoListResponse,
    ProjetoResponse,
    ProjetoUpdate,
)
from app.api.services._helpers import iso as _iso
from app.db.session import get_session
from app.repositories.pessoal.freela_repository import FreelaRepository

from ._base import FreelaError, _chamar_llm, _projeto_to_resp, _uuid, _uuid_opt


async def criar_projeto(payload: ProjetoCreate) -> ProjetoResponse:
    if not payload.titulo.strip():
        raise FreelaError("O projeto precisa de um título.")
    if not payload.descricao.strip():
        raise FreelaError("Cole a descrição do projeto.")
    dados = payload.model_dump()
    dados["plataforma_id"] = _uuid_opt(dados.get("plataforma_id"), "plataforma_id")
    dados["cliente_id"] = _uuid_opt(dados.get("cliente_id"), "cliente_id")
    async with get_session() as session:
        projeto = await FreelaRepository(session).create_projeto(dados)
        return _projeto_to_resp(projeto)


async def listar_projetos() -> ProjetoListResponse:
    async with get_session() as session:
        linhas = await FreelaRepository(session).listar_projetos()
    items = []
    for projeto, cliente_nome, qtd, pago_usd in linhas:
        analise = projeto.analise_json or {}
        items.append(
            ProjetoListItem(
                id=str(projeto.id),
                titulo=projeto.titulo,
                cliente_nome=cliente_nome,
                status_no_site=projeto.status_no_site,
                faixa_orcamento_min=float(projeto.faixa_orcamento_min) if projeto.faixa_orcamento_min is not None else None,
                faixa_orcamento_max=float(projeto.faixa_orcamento_max) if projeto.faixa_orcamento_max is not None else None,
                n_propostas_concorrentes=projeto.n_propostas_concorrentes,
                fit_score=analise.get("fit_score"),
                risco=analise.get("risco"),
                quadrante=analise.get("quadrante"),
                preco_status=(analise.get("veredito_preco") or {}).get("status"),
                estimativa=analise.get("estimativa"),
                tem_analise=projeto.analise_json is not None,
                qtd_propostas=qtd,
                cliente_recorrente=pago_usd > 0,
                cliente_pago_usd=round(pago_usd, 2),
                created_at=_iso(projeto.created_at),
            )
        )
    # Fila de oportunidades: cliente recorrente vale ouro (vem primeiro), depois
    # maior fit (sem análise vai pro fim).
    items.sort(
        key=lambda i: (not i.cliente_recorrente, i.fit_score is None, -(i.fit_score or 0))
    )
    return ProjetoListResponse(items=items, total=len(items))


async def get_projeto(projeto_id: str) -> ProjetoResponse:
    async with get_session() as session:
        projeto = await FreelaRepository(session).get_projeto(_uuid(projeto_id))
        if projeto is None:
            raise FreelaError("Projeto não encontrado.")
        return _projeto_to_resp(projeto)


async def atualizar_projeto(projeto_id: str, payload: ProjetoUpdate) -> ProjetoResponse:
    dados = dict(payload.model_dump(exclude_unset=True))
    if "plataforma_id" in dados:
        dados["plataforma_id"] = _uuid_opt(dados["plataforma_id"], "plataforma_id")
    if "cliente_id" in dados:
        dados["cliente_id"] = _uuid_opt(dados["cliente_id"], "cliente_id")
    async with get_session() as session:
        projeto = await FreelaRepository(session).update_projeto(_uuid(projeto_id), dados)
        if projeto is None:
            raise FreelaError("Projeto não encontrado.")
        return _projeto_to_resp(projeto)


async def deletar_projeto(projeto_id: str) -> None:
    async with get_session() as session:
        ok = await FreelaRepository(session).delete_projeto(_uuid(projeto_id))
        if not ok:
            raise FreelaError("Projeto não encontrado.")


async def extrair_projeto(texto: str) -> ExtrairProjetoResponse:
    """Lê o texto colado da Workana e devolve campos pré-preenchidos (não salva)."""
    if not texto.strip():
        raise FreelaError("Cole o texto do projeto pra extrair.")

    prompt = construir_prompt_extracao(texto)
    resposta = _chamar_llm(prompt, operacao="extrair")
    dados = parse_extracao(resposta)
    if dados is None:
        raise FreelaError("A IA não conseguiu extrair os campos. Preencha na mão.")
    return dados
