"""Service de Recorrências — cadastro e leitura das despesas/receitas fixas."""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select

from app.api.schemas.financas import (
    RecorrenciaCreate,
    RecorrenciaListResponse,
    RecorrenciaResponse,
    RecorrenciaUpdate,
)
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.conta import Conta
from app.db.models.financas.recorrencia import Recorrencia
from app.db.models.financas.transacao import Transacao
from app.db.session import get_session

TIPOS_RECORRENCIA = ("despesa", "receita")


class RecorrenciaError(Exception):
    """Erro de negócio de Recorrências — vira HTTP 400/404 no router."""


def _iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise RecorrenciaError(f"{campo} inválido: {valor!r}")


def _to_response(r: Recorrencia) -> RecorrenciaResponse:
    return RecorrenciaResponse(
        id=str(r.id),
        usuario_id=str(r.usuario_id),
        descricao=r.descricao,
        tipo=r.tipo,
        valor_estimado=r.valor_estimado,
        dia_vencimento=r.dia_vencimento,
        frequencia=r.frequencia,
        categoria_id=str(r.categoria_id) if r.categoria_id else None,
        conta_id=str(r.conta_id) if r.conta_id else None,
        ativa=r.ativa,
        created_at=_iso(r.created_at),
        updated_at=_iso(r.updated_at),
    )


async def criar_recorrencia(payload: RecorrenciaCreate) -> RecorrenciaResponse:
    if not payload.descricao.strip():
        raise RecorrenciaError("A recorrência precisa de uma descrição.")
    if payload.tipo not in TIPOS_RECORRENCIA:
        raise RecorrenciaError(
            f"Tipo inválido: {payload.tipo!r}. Use 'despesa' ou 'receita'."
        )

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )
    conta_id = _uuid(payload.conta_id, campo="conta_id") if payload.conta_id else None

    async with get_session() as session:
        if categoria_id and await session.get(Categoria, categoria_id) is None:
            raise RecorrenciaError("Categoria não encontrada.")
        if conta_id is not None:
            conta = await session.get(Conta, conta_id)
            if conta is None:
                raise RecorrenciaError("Conta não encontrada.")
            if conta.usuario_id != usuario_id:
                raise RecorrenciaError("A conta não pertence a esse usuário.")

        rec = Recorrencia(
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            tipo=payload.tipo,
            valor_estimado=payload.valor_estimado,
            dia_vencimento=payload.dia_vencimento,
            frequencia=payload.frequencia,
            categoria_id=categoria_id,
            conta_id=conta_id,
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return _to_response(rec)


async def tornar_recorrente(
    transacao_id: str, usuario_id_sessao: str, dia_vencimento: Optional[int] = None
) -> RecorrenciaResponse:
    """Cria uma conta fixa (recorrência) a partir de uma transação/boleto e
    liga a transação atual à recorrência, pra o cron não gerar uma 2ª prevista
    deste mês. O dia de vencimento vem do boleto (ou do informado)."""
    from datetime import date

    tid = _uuid(transacao_id)
    uid = _uuid(usuario_id_sessao, campo="usuario_id")
    async with get_session() as session:
        t = await session.get(Transacao, tid)
        if t is None:
            raise RecorrenciaError("Transação não encontrada.")
        if t.usuario_id != uid:
            raise RecorrenciaError("A transação não pertence a esse usuário.")

        dia = dia_vencimento or (
            t.data_vencimento.day if t.data_vencimento else date.today().day
        )
        dia = max(1, min(int(dia), 31))

        rec = Recorrencia(
            usuario_id=uid,
            descricao=t.descricao,
            tipo=t.tipo,
            valor_estimado=t.valor_total,
            dia_vencimento=dia,
            frequencia="mensal",
            categoria_id=t.categoria_id,
        )
        session.add(rec)
        await session.flush()
        # Liga a transação à recorrência → idempotência do cron neste mês.
        t.recorrencia_id = rec.id
        await session.commit()
        await session.refresh(rec)
        return _to_response(rec)


async def atualizar_recorrencia(
    recorrencia_id: str, payload: RecorrenciaUpdate
) -> RecorrenciaResponse:
    dados = payload.model_dump(exclude_unset=True)
    if "tipo" in dados and dados["tipo"] is not None:
        if dados["tipo"] not in TIPOS_RECORRENCIA:
            raise RecorrenciaError(
                f"Tipo inválido: {dados['tipo']!r}. Use 'despesa' ou 'receita'."
            )
    if "descricao" in dados and dados["descricao"] is not None:
        if not dados["descricao"].strip():
            raise RecorrenciaError("A descrição não pode ficar vazia.")
        dados["descricao"] = dados["descricao"].strip()

    async with get_session() as session:
        rec = await session.get(Recorrencia, _uuid(recorrencia_id))
        if rec is None:
            raise RecorrenciaError("Recorrência não encontrada.")

        if dados.get("categoria_id"):
            cid = _uuid(dados["categoria_id"], campo="categoria_id")
            if await session.get(Categoria, cid) is None:
                raise RecorrenciaError("Categoria não encontrada.")
            dados["categoria_id"] = cid
        if dados.get("conta_id"):
            coid = _uuid(dados["conta_id"], campo="conta_id")
            conta = await session.get(Conta, coid)
            if conta is None:
                raise RecorrenciaError("Conta não encontrada.")
            if conta.usuario_id != rec.usuario_id:
                raise RecorrenciaError("A conta não pertence a esse usuário.")
            dados["conta_id"] = coid

        for campo, valor in dados.items():
            setattr(rec, campo, valor)
        await session.commit()
        await session.refresh(rec)
        return _to_response(rec)


async def excluir_recorrencia(recorrencia_id: str) -> None:
    async with get_session() as session:
        rec = await session.get(Recorrencia, _uuid(recorrencia_id))
        if rec is None:
            raise RecorrenciaError("Recorrência não encontrada.")
        # Transações já geradas ficam (recorrencia_id vira NULL pela FK).
        await session.delete(rec)
        await session.commit()


async def listar_recorrencias(usuario_id: str) -> RecorrenciaListResponse:
    uid = _uuid(usuario_id, campo="usuario_id")
    async with get_session() as session:
        stmt = (
            select(Recorrencia)
            .where(Recorrencia.usuario_id == uid)
            .order_by(Recorrencia.dia_vencimento)
        )
        recs = (await session.execute(stmt)).scalars().all()
        items = [_to_response(r) for r in recs]
    return RecorrenciaListResponse(items=items, total=len(items))
