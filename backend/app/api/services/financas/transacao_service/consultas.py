from __future__ import annotations

from ._base import *  # noqa: F401,F403  (imports/TransacaoError compartilhados)
from ._base import (  # noqa: F401  (helpers privados)
    _uuid, _iso, _to_response, _buscar_conta, _validar_categoria,
    _finalizar_transacao, _checar_status, _intervalo_mes,
)


async def sugestao_conta_pagamento(
    transacao_id: str, usuario_id_sessao: str
) -> dict:
    """Sugere a conta pra pagar uma conta a pagar: a última usada pra pagar o
    mesmo beneficiário. Retorna {conta_id, conta_nome} (None se não houver)."""
    tid = _uuid(transacao_id)
    uid = _uuid(usuario_id_sessao, campo="usuario_id")
    async with get_session() as session:
        repo = TransacaoRepository(session)
        t = await repo.get(tid)
        if t is None:
            raise TransacaoError("Transação não encontrada.")
        if t.usuario_id != uid:
            raise TransacaoError("A transação não pertence a esse usuário.")
        conta_id = await repo.ultima_conta_por_descricao(uid, t.descricao)
        nome = None
        if conta_id is not None:
            conta = await session.get(Conta, conta_id)
            nome = conta.nome if conta is not None else None
    return {
        "conta_id": str(conta_id) if conta_id else None,
        "conta_nome": nome,
    }


async def get_transacao(transacao_id: str) -> TransacaoResponse:
    async with get_session() as session:
        transacao = await TransacaoRepository(session).get(_uuid(transacao_id))
        if transacao is None:
            raise TransacaoError("Transação não encontrada.")
        return _to_response(transacao)



async def listar_transacoes(
    usuario_id: str,
    *,
    ano: Optional[int] = None,
    mes: Optional[int] = None,
    conta_id: Optional[str] = None,
    categoria_id: Optional[str] = None,
    tipo: Optional[str] = None,
    status: Optional[List[str]] = None,
    busca: Optional[str] = None,
    por_vencimento: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> TransacaoListResponse:
    """Lista filtrável de transações para o dashboard (mais novas primeiro)."""
    uid = _uuid(usuario_id, campo="usuario_id")
    inicio, proximo = _intervalo_mes(ano, mes)
    cid = _uuid(conta_id, campo="conta_id") if conta_id else None
    catid = _uuid(categoria_id, campo="categoria_id") if categoria_id else None
    if tipo is not None and tipo not in ("despesa", "receita"):
        raise TransacaoError(f"Tipo inválido: {tipo!r}. Use despesa ou receita.")
    if status:
        invalidos = [s for s in status if s not in STATUS_TRANSACAO]
        if invalidos:
            raise TransacaoError(f"Status inválido: {', '.join(invalidos)}.")
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    termo = busca.strip() if busca and busca.strip() else None

    async with get_session() as session:
        repo = TransacaoRepository(session)
        itens, total = await repo.listar(
            uid,
            inicio=inicio,
            proximo_mes=proximo,
            conta_id=cid,
            categoria_id=catid,
            tipo=tipo,
            status=status,
            busca=termo,
            por_vencimento=por_vencimento,
            limit=limit,
            offset=offset,
        )

        conta_ids = {p.conta_id for t in itens for p in t.pagamentos}
        cat_ids = {t.categoria_id for t in itens if t.categoria_id}
        contas_nome: dict = {}
        if conta_ids:
            rows = await session.execute(
                select(Conta.id, Conta.nome).where(Conta.id.in_(conta_ids))
            )
            contas_nome = {cid_: nome for cid_, nome in rows.all()}
        cat_nome: dict = {}
        if cat_ids:
            rows = await session.execute(
                select(Categoria.id, Categoria.nome).where(Categoria.id.in_(cat_ids))
            )
            cat_nome = {cid_: nome for cid_, nome in rows.all()}

        items = [
            TransacaoListItem(
                id=str(t.id),
                tipo=t.tipo,
                descricao=t.descricao,
                valor_total=t.valor_total,
                data_competencia=t.data_competencia,
                data_pagamento=t.data_pagamento,
                data_vencimento=t.data_vencimento,
                multa_percentual=t.multa_percentual,
                juros_mensal_percentual=t.juros_mensal_percentual,
                encargos_pagos=t.encargos_pagos,
                linha_digitavel=t.linha_digitavel,
                desconto_valor=t.desconto_valor,
                desconto_ate=t.desconto_ate,
                status=t.status,
                categoria_id=str(t.categoria_id) if t.categoria_id else None,
                categoria_nome=cat_nome.get(t.categoria_id),
                recorrencia_id=str(t.recorrencia_id) if t.recorrencia_id else None,
                contas=[contas_nome.get(p.conta_id, "?") for p in t.pagamentos],
            )
            for t in itens
        ]

    return TransacaoListResponse(
        items=items, total=total, limit=limit, offset=offset
    )



async def ultima_transacao(usuario_id: str) -> Optional[TransacaoResponse]:
    """A transação criada mais recentemente pelo usuário (pro /desfazer do bot).
    Ordena por created_at — é o 'último lançamento', não a competência mais nova."""
    uid = _uuid(usuario_id, campo="usuario_id")
    async with get_session() as session:
        from sqlalchemy.orm import selectinload

        stmt = (
            select(Transacao)
            .options(
                selectinload(Transacao.itens),
                selectinload(Transacao.pagamentos),
            )
            .where(Transacao.usuario_id == uid)
            .order_by(Transacao.created_at.desc())
            .limit(1)
        )
        t = await session.scalar(stmt)
        return _to_response(t) if t is not None else None



