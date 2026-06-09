from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import Sessao, Usuario
from app.db.session import dispose_engine, get_session


async def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step 1 (usuarios + sessoes, schema auth)")
    print("━" * 60)

    email = f"teste_{uuid.uuid4().hex[:8]}@reativesystems.com.br"
    usuario_id = None
    try:
        # ── 1. Usuario: defaults (ativo=True, twofa=False) ────────────
        print("\n→ Test 1: cria usuario (defaults)")
        async with get_session() as session:
            u = Usuario(email=email, senha_hash="x" * 60, nome="Teste")
            session.add(u)
            await session.commit()
            await session.refresh(u)
            usuario_id = u.id
            assert isinstance(u.id, uuid.UUID)
            assert u.ativo is True
            assert u.twofa_ativado is False
            assert u.ultimo_login is None
            assert u.created_at is not None
            print(f"   usuario id={usuario_id} ativo={u.ativo} 2fa={u.twofa_ativado}")

        # ── 2. Email único → IntegrityError ───────────────────────────
        print("\n→ Test 2: email duplicado barra (unique)")
        try:
            async with get_session() as session:
                session.add(Usuario(email=email, senha_hash="y" * 60, nome="Clone"))
                await session.commit()
            assert False, "deveria ter barrado email duplicado"
        except IntegrityError:
            print("   barrou email duplicado ✓")

        # ── 3. Sessao vinculada ao usuario ────────────────────────────
        print("\n→ Test 3: cria sessao")
        sessao_id = None
        async with get_session() as session:
            s = Sessao(
                usuario_id=usuario_id,
                token_hash="a" * 64,
                expira_em=datetime.now(timezone.utc) + timedelta(days=7),
                ip="127.0.0.1",
                user_agent="pytest",
            )
            session.add(s)
            await session.commit()
            await session.refresh(s)
            sessao_id = s.id
            assert s.revogada is False
            assert s.ultimo_uso is not None
            print(f"   sessao id={sessao_id} revogada={s.revogada}")

        # ── 4. CASCADE: deletar o usuario leva a sessao junto ─────────
        print("\n→ Test 4: delete usuario → sessao em cascata (FK ondelete)")
        async with get_session() as session:
            u = await session.scalar(select(Usuario).where(Usuario.id == usuario_id))
            await session.delete(u)
            await session.commit()
        usuario_id = None
        async with get_session() as session:
            sumiu = await session.scalar(select(Sessao).where(Sessao.id == sessao_id))
            assert sumiu is None, "sessao deveria sumir junto com o usuario (CASCADE)"
            print("   usuario e sessao removidos (CASCADE) ✓")

    finally:
        async with get_session() as session:
            if usuario_id:
                u = await session.scalar(select(Usuario).where(Usuario.id == usuario_id))
                if u:
                    await session.delete(u)
                    await session.commit()

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step 1 funcionando!")
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
