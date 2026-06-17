"""Service de Comprovantes — upload pro MinIO + registro, com dedup por hash."""
from __future__ import annotations

import asyncio
import hashlib
import os
import uuid

from sqlalchemy import select

from app.api.schemas.financas import ComprovanteListResponse, ComprovanteResponse
from app.db.models.financas.comprovante import (
    BUCKET_POR_TIPO,
    TIPOS_COMPROVANTE,
    Comprovante,
)
from app.db.models.financas.transacao import Transacao
from app.db.session import get_session
from app.utils.s3_storage import get_storage


class ComprovanteError(Exception):
    """Erro de negócio de Comprovantes — vira HTTP 400/404 no router."""


from app.api.services.financas._common import iso as _iso


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise ComprovanteError(f"{campo} inválido: {valor!r}")


def _to_response(c: Comprovante, *, com_url: bool = False) -> ComprovanteResponse:
    url = None
    if com_url:
        url = get_storage().presigned_url(c.bucket, c.arquivo_path)
    return ComprovanteResponse(
        id=str(c.id),
        usuario_id=str(c.usuario_id),
        transacao_id=str(c.transacao_id) if c.transacao_id else None,
        tipo=c.tipo,
        bucket=c.bucket,
        arquivo_path=c.arquivo_path,
        nome_original=c.nome_original,
        content_type=c.content_type,
        tamanho=c.tamanho,
        hash=c.hash,
        url=url,
        created_at=_iso(c.created_at),
        updated_at=_iso(c.updated_at),
    )


async def salvar_comprovante(
    *,
    usuario_id: str,
    tipo: str,
    conteudo: bytes,
    nome_original: str | None = None,
    content_type: str | None = None,
    transacao_id: str | None = None,
) -> ComprovanteResponse:
    if tipo not in TIPOS_COMPROVANTE:
        raise ComprovanteError(
            f"Tipo inválido: {tipo!r}. Use um de: {', '.join(TIPOS_COMPROVANTE)}."
        )
    if not conteudo:
        raise ComprovanteError("Arquivo vazio.")

    uid = _uuid(usuario_id, campo="usuario_id")
    tx_id = _uuid(transacao_id, campo="transacao_id") if transacao_id else None
    h = hashlib.sha256(conteudo).hexdigest()
    bucket = BUCKET_POR_TIPO[tipo]

    async with get_session() as session:
        # Dedup: mesmo arquivo (hash) do mesmo usuário → devolve o existente.
        existente = await session.scalar(
            select(Comprovante).where(
                Comprovante.usuario_id == uid, Comprovante.hash == h
            )
        )
        if existente is not None:
            return _to_response(existente)

        if tx_id is not None:
            tx = await session.get(Transacao, tx_id)
            if tx is None:
                raise ComprovanteError("Transação não encontrada.")
            if tx.usuario_id != uid:
                raise ComprovanteError("A transação não pertence a esse usuário.")

        ext = os.path.splitext(nome_original or "")[1].lower()
        key = f"{uid}/{h}{ext}"
        # boto3 é síncrono → roda fora do event loop
        await asyncio.to_thread(
            get_storage().upload_bytes, bucket, key, conteudo, content_type
        )

        comp = Comprovante(
            usuario_id=uid,
            transacao_id=tx_id,
            tipo=tipo,
            bucket=bucket,
            arquivo_path=key,
            nome_original=nome_original,
            content_type=content_type,
            tamanho=len(conteudo),
            hash=h,
        )
        session.add(comp)
        await session.commit()
        await session.refresh(comp)
        return _to_response(comp)


async def listar_por_transacao(transacao_id: str) -> ComprovanteListResponse:
    tx_id = _uuid(transacao_id, campo="transacao_id")
    async with get_session() as session:
        stmt = (
            select(Comprovante)
            .where(Comprovante.transacao_id == tx_id)
            .order_by(Comprovante.created_at.desc())
        )
        comps = (await session.execute(stmt)).scalars().all()
        items = [_to_response(c, com_url=True) for c in comps]
    return ComprovanteListResponse(items=items, total=len(items))


async def listar_por_usuario(
    usuario_id: str, *, tipo: str | None = None
) -> ComprovanteListResponse:
    uid = _uuid(usuario_id, campo="usuario_id")
    if tipo is not None and tipo not in TIPOS_COMPROVANTE:
        raise ComprovanteError(f"Tipo inválido: {tipo!r}.")
    async with get_session() as session:
        stmt = (
            select(Comprovante)
            .where(Comprovante.usuario_id == uid)
            .order_by(Comprovante.created_at.desc())
        )
        if tipo is not None:
            stmt = stmt.where(Comprovante.tipo == tipo)
        comps = (await session.execute(stmt)).scalars().all()
        items = [_to_response(c, com_url=True) for c in comps]
    return ComprovanteListResponse(items=items, total=len(items))
