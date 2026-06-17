"""Service de Categorias — CRUD da hierarquia de categorias/subverbas.

Categorias são compartilhadas (sem usuario_id). A árvore é montada em Python
a partir da lista flat (suporta qualquer profundidade sem N+1).
"""
from __future__ import annotations

import uuid

from app.api.schemas.financas import (
    CategoriaCreate,
    CategoriaResponse,
    CategoriaTreeItem,
    CategoriaTreeResponse,
    CategoriaUpdate,
)
from app.db.models.financas.categoria import Categoria
from app.db.session import get_session
from app.repositories.financas.categoria_repository import CategoriaRepository


class CategoriaError(Exception):
    """Erro de negócio de Categorias — vira HTTP 400/404 no router."""


from app.api.services.financas._common import iso as _iso


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise CategoriaError(f"{campo} inválido: {valor!r}")


def _to_response(c: Categoria) -> CategoriaResponse:
    return CategoriaResponse(
        id=str(c.id),
        nome=c.nome,
        categoria_pai_id=str(c.categoria_pai_id) if c.categoria_pai_id else None,
        ativa=c.ativa,
        created_at=_iso(c.created_at),
        updated_at=_iso(c.updated_at),
    )


def _build_tree(categorias: list[Categoria]) -> list[CategoriaTreeItem]:
    nodes: dict[uuid.UUID, CategoriaTreeItem] = {
        c.id: CategoriaTreeItem(id=str(c.id), nome=c.nome, ativa=c.ativa, filhos=[])
        for c in categorias
    }
    raizes: list[CategoriaTreeItem] = []
    for c in categorias:  # já vem ordenado por nome → irmãos saem em ordem
        node = nodes[c.id]
        if c.categoria_pai_id and c.categoria_pai_id in nodes:
            nodes[c.categoria_pai_id].filhos.append(node)
        else:
            raizes.append(node)
    return raizes


def _descendentes(categoria_id: uuid.UUID, todas: list[Categoria]) -> set[uuid.UUID]:
    filhos_por_pai: dict[uuid.UUID | None, list[uuid.UUID]] = {}
    for c in todas:
        filhos_por_pai.setdefault(c.categoria_pai_id, []).append(c.id)
    desc: set[uuid.UUID] = set()
    pilha = [categoria_id]
    while pilha:
        atual = pilha.pop()
        for filho in filhos_por_pai.get(atual, []):
            if filho not in desc:
                desc.add(filho)
                pilha.append(filho)
    return desc


async def criar_categoria(payload: CategoriaCreate) -> CategoriaResponse:
    if not payload.nome.strip():
        raise CategoriaError("A categoria precisa de um nome.")

    pai_id = None
    async with get_session() as session:
        repo = CategoriaRepository(session)
        if payload.categoria_pai_id:
            pai_id = _uuid(payload.categoria_pai_id, campo="categoria_pai_id")
            if await repo.get(pai_id) is None:
                raise CategoriaError("Categoria pai não encontrada.")

        categoria = await repo.create({
            "nome": payload.nome.strip(),
            "categoria_pai_id": pai_id,
        })
        return _to_response(categoria)


async def listar_arvore() -> CategoriaTreeResponse:
    async with get_session() as session:
        todas = await CategoriaRepository(session).listar_todas()
    return CategoriaTreeResponse(items=_build_tree(todas), total=len(todas))


async def get_categoria(categoria_id: str) -> CategoriaResponse:
    async with get_session() as session:
        categoria = await CategoriaRepository(session).get(_uuid(categoria_id))
        if categoria is None:
            raise CategoriaError("Categoria não encontrada.")
        return _to_response(categoria)


async def atualizar_categoria(
    categoria_id: str, payload: CategoriaUpdate
) -> CategoriaResponse:
    cid = _uuid(categoria_id)
    bruto = payload.model_dump(exclude_unset=True)
    dados: dict = {}

    if "nome" in bruto:
        if not bruto["nome"] or not bruto["nome"].strip():
            raise CategoriaError("O nome da categoria não pode ficar vazio.")
        dados["nome"] = bruto["nome"].strip()
    if "ativa" in bruto:
        dados["ativa"] = bruto["ativa"]

    async with get_session() as session:
        repo = CategoriaRepository(session)

        if "categoria_pai_id" in bruto:
            novo_pai = bruto["categoria_pai_id"]
            if novo_pai is None:
                dados["categoria_pai_id"] = None       # vira raiz
            else:
                pai_id = _uuid(novo_pai, campo="categoria_pai_id")
                if pai_id == cid:
                    raise CategoriaError("Uma categoria não pode ser pai de si mesma.")
                todas = await repo.listar_todas()
                if pai_id not in {c.id for c in todas}:
                    raise CategoriaError("Categoria pai não encontrada.")
                if pai_id in _descendentes(cid, todas):
                    raise CategoriaError(
                        "Movimento criaria um ciclo: o pai escolhido é "
                        "descendente desta categoria."
                    )
                dados["categoria_pai_id"] = pai_id

        categoria = await repo.update(cid, dados)
        if categoria is None:
            raise CategoriaError("Categoria não encontrada.")
        return _to_response(categoria)


async def deletar_categoria(categoria_id: str) -> bool:
    async with get_session() as session:
        ok = await CategoriaRepository(session).delete(_uuid(categoria_id))
        if not ok:
            raise CategoriaError("Categoria não encontrada.")
        return True
