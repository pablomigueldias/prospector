"""CRUD/publicar do agente LinkedIn (autenticado). Toda escrita passa por aqui:
recalcula a contagem de caracteres e valida os enums (conta/status/...)."""
from __future__ import annotations

from datetime import UTC, datetime

from app.api.schemas.linkedin import (
    LinkedinPostCreate,
    LinkedinPostOut,
    LinkedinPostUpdate,
)
from app.db.models.linkedin.post import (
    CONTA_LINKEDIN,
    FORMATO_LINKEDIN,
    STATUS_LINKEDIN,
)
from app.db.session import get_session
from app.repositories.linkedin_repository import LinkedinRepository

from ._base import LinkedinError, _uuid, contar_chars, to_out


def _validar(dados: dict) -> None:
    if dados.get("conta") and dados["conta"] not in CONTA_LINKEDIN:
        raise LinkedinError(f"conta inválida: {dados['conta']!r}")
    if dados.get("formato") and dados["formato"] not in FORMATO_LINKEDIN:
        raise LinkedinError(f"formato inválido: {dados['formato']!r}")


def _aplicar_chars(post, dados: dict) -> None:
    """Recalcula char_count quando hook/body/cta mudam (usa o valor atual do post
    pros campos não enviados no patch)."""
    if not any(c in dados for c in ("hook", "body", "cta")):
        return
    hook = dados.get("hook", getattr(post, "hook", None))
    body = dados.get("body", getattr(post, "body", None))
    cta = dados.get("cta", getattr(post, "cta", None))
    dados["char_count"] = contar_chars(hook, body, cta)


async def listar(
    status: str | None = None, conta: str | None = None
) -> list[LinkedinPostOut]:
    if status and status not in STATUS_LINKEDIN:
        raise LinkedinError(f"status inválido: {status!r}")
    if conta and conta not in CONTA_LINKEDIN:
        raise LinkedinError(f"conta inválida: {conta!r}")
    async with get_session() as session:
        posts = await LinkedinRepository(session).listar(status=status, conta=conta)
        return [to_out(p) for p in posts]


async def get(post_id: str) -> LinkedinPostOut:
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        post = await LinkedinRepository(session).get(pid)
        if post is None:
            raise LinkedinError("Post não encontrado.")
        return to_out(post)


async def criar(payload: LinkedinPostCreate) -> LinkedinPostOut:
    dados = payload.model_dump(exclude_none=True)
    _validar(dados)
    _aplicar_chars(None, dados)
    async with get_session() as session:
        post = await LinkedinRepository(session).create(dados)
        return to_out(post)


async def atualizar(post_id: str, payload: LinkedinPostUpdate) -> LinkedinPostOut:
    pid = _uuid(post_id, "post_id")
    dados = payload.model_dump(exclude_unset=True, exclude_none=True)
    _validar(dados)
    async with get_session() as session:
        repo = LinkedinRepository(session)
        atual = await repo.get(pid)
        if atual is None:
            raise LinkedinError("Post não encontrado.")
        _aplicar_chars(atual, dados)
        post = await repo.update(pid, dados)
        return to_out(post)


async def mudar_status(post_id: str, status: str) -> LinkedinPostOut:
    if status not in STATUS_LINKEDIN:
        raise LinkedinError(f"status inválido: {status!r}")
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        repo = LinkedinRepository(session)
        atual = await repo.get(pid)
        if atual is None:
            raise LinkedinError("Post não encontrado.")
        dados: dict = {"status": status}
        # Marcar "publicado" pela 1ª vez carimba quando o Pablo postou na mão.
        if status == "publicado" and atual.published_at is None:
            dados["published_at"] = datetime.now(UTC)
        post = await repo.update(pid, dados)
        return to_out(post)


async def deletar(post_id: str) -> None:
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        ok = await LinkedinRepository(session).delete(pid)
        if not ok:
            raise LinkedinError("Post não encontrado.")
