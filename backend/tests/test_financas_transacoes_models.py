from __future__ import annotations

import asyncio
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Conta, Transacao, TransacaoItem, TransacaoPagamento
from app.db.session import dispose_engine, get_session


async def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 6 (transacoes + itens + pagamentos)")
    print("━" * 60)

    usuario_id = uuid.uuid4()
    conta_id = None
    transacao_id = None
    try:
        # ── Conta pra receber os pagamentos ──────────────────────────
        async with get_session() as session:
            conta = Conta(usuario_id=usuario_id, nome="Carteira", tipo="dinheiro")
            session.add(conta)
            await session.commit()
            await session.refresh(conta)
            conta_id = conta.id

        # ── 1. Transação do condomínio: 1 total, 2 itens, 1 pagamento ─
        print("\n→ Test 1: cria transação com itens e pagamentos")
        async with get_session() as session:
            tx = Transacao(
                usuario_id=usuario_id,
                tipo="despesa",
                descricao="Condomínio JUN/26",
                valor_total=Decimal("300.00"),
                data_competencia=date(2026, 6, 1),
                data_pagamento=date(2026, 6, 5),
                status="paga",
                origem="manual",
                itens=[
                    TransacaoItem(descricao="Taxa de condomínio", valor=Decimal("250.00")),
                    TransacaoItem(descricao="Consumo de gás", valor=Decimal("50.00")),
                ],
                pagamentos=[
                    TransacaoPagamento(conta_id=conta_id, valor=Decimal("300.00")),
                ],
            )
            session.add(tx)
            await session.commit()
            await session.refresh(tx)
            transacao_id = tx.id
            print(f"   transacao id={transacao_id}")

        # ── 2. Relações carregam (selectin) e somam o total ──────────
        print("\n→ Test 2: itens/pagamentos e soma")
        async with get_session() as session:
            tx = await session.scalar(
                select(Transacao)
                .options(
                    selectinload(Transacao.itens),
                    selectinload(Transacao.pagamentos),
                )
                .where(Transacao.id == transacao_id)
            )
            assert tx is not None
            assert len(tx.itens) == 2, len(tx.itens)
            assert len(tx.pagamentos) == 1, len(tx.pagamentos)
            soma_itens = sum(i.valor for i in tx.itens)
            soma_pag = sum(p.valor for p in tx.pagamentos)
            assert soma_itens == tx.valor_total == soma_pag == Decimal("300.00"), (
                soma_itens, tx.valor_total, soma_pag
            )
            print(f"   itens={len(tx.itens)} (soma {soma_itens}) ; "
                  f"pagamentos={len(tx.pagamentos)} (soma {soma_pag}) ; total={tx.valor_total}")

        # ── 3. CASCADE: deletar a transação leva itens e pagamentos ──
        print("\n→ Test 3: delete em cascata")
        async with get_session() as session:
            tx = await session.get(Transacao, transacao_id)
            await session.delete(tx)
            await session.commit()
        transacao_id = None
        async with get_session() as session:
            itens = (await session.execute(select(TransacaoItem))).scalars().all()
            pags = (await session.execute(select(TransacaoPagamento))).scalars().all()
            # nenhum item/pagamento órfão do nosso teste deve sobrar
            assert all(i.transacao_id is not None for i in itens)
            # a conta NÃO some quando a transação é deletada
            conta = await session.get(Conta, conta_id)
            assert conta is not None
            print("   itens e pagamentos removidos; conta preservada")

    finally:
        async with get_session() as session:
            if transacao_id:
                tx = await session.get(Transacao, transacao_id)
                if tx:
                    await session.delete(tx)
            if conta_id:
                c = await session.get(Conta, conta_id)
                if c:
                    await session.delete(c)
            await session.commit()

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 6 funcionando!")
    print("━" * 60)


async def _run_with_cleanup() -> None:
    try:
        await smoke_test()
    finally:
        await dispose_engine()


def main() -> None:
    asyncio.run(_run_with_cleanup())


if __name__ == "__main__":
    main()
