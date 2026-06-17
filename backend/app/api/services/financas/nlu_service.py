"""Service do NLU — interpreta texto livre e devolve um rascunho de transação.

Não persiste: o bot mostra um card de confirmação (Fase 5) antes de gravar.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date

from app.analyzers.nlu import extrator
from app.analyzers.nlu.parser import parse_nlu
from app.analyzers.nlu.prompt_builder import construir_prompt
from app.api.schemas.financas import InterpretacaoResponse
from app.db.session import get_session
from app.repositories.financas.categoria_repository import CategoriaRepository
from app.repositories.financas.conta_repository import ContaRepository


class NLUError(Exception):
    """Erro de negócio do NLU — vira HTTP 400 no router."""


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise NLUError(f"{campo} inválido: {valor!r}")


def _casar(guess: str | None, itens: list) -> tuple[str | None, str | None]:
    """Casa o nome chutado pelo LLM com a lista (id, nome): exato (case-insensitive)
    e depois por substring. Devolve (id, nome) ou (None, None)."""
    if not guess:
        return None, None
    g = guess.strip().lower()
    for obj in itens:
        if obj.nome.lower() == g:
            return str(obj.id), obj.nome
    for obj in itens:
        if g in obj.nome.lower() or obj.nome.lower() in g:
            return str(obj.id), obj.nome
    return None, None


async def interpretar_texto(usuario_id: str, texto: str) -> InterpretacaoResponse:
    if not texto or not texto.strip():
        raise NLUError("Manda a frase do gasto/receita.")
    uid = _uuid(usuario_id, campo="usuario_id")

    async with get_session() as session:
        contas = await ContaRepository(session).listar(uid)
        categorias = await CategoriaRepository(session).listar_todas()

    prompt = construir_prompt(
        texto.strip(),
        contas=[c.nome for c in contas],
        categorias=[c.nome for c in categorias],
        hoje=date.today(),
    )
    cru = await asyncio.to_thread(extrator.interpretar_llm, prompt)
    res = parse_nlu(cru)
    if res is None:
        raise NLUError("Não entendi a frase. Tenta reescrever de outro jeito.")
    if res.tipo not in ("despesa", "receita"):
        raise NLUError(f"Tipo interpretado inválido: {res.tipo!r}.")

    conta_id, conta_nome = _casar(res.conta, contas)
    categoria_id, categoria_nome = _casar(res.categoria, categorias)

    return InterpretacaoResponse(
        tipo=res.tipo,
        valor=res.valor,
        descricao=res.descricao,
        data=res.data or date.today(),
        conta_id=conta_id,
        conta_nome=conta_nome,
        categoria_id=categoria_id,
        categoria_nome=categoria_nome,
        texto_original=texto.strip(),
    )
