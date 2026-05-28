from __future__ import annotations

import asyncio
import uuid

from app.db.models import Contato, Empresa, Socio
from app.db.session import dispose_engine, get_session
from app.repositories import ContatoRepository, EmpresaRepository


CNPJ_TESTE = "00000000000191"


async def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — Passo 1 (Postgres + repositórios)")
    print("━" * 60)

    # ── 1. Limpa qualquer empresa-teste anterior ─────────────────
    async with get_session() as session:
        repo = EmpresaRepository(session)
        existing = await repo.find_by_cnpj(CNPJ_TESTE)
        if existing:
            print(f" Limpando empresa-teste anterior (id={existing.id})")
            await session.delete(existing)
            await session.commit()

    # ── 2. INSERT inicial ────────────────────────────────────────
    print("\n→ Test 1: INSERT inicial")
    async with get_session() as session:
        empresa = Empresa(
            nome="Padaria do Teste",
            razao_social="Padaria do Teste Ltda",
            cnpj=CNPJ_TESTE,
            cidade="São Paulo",
            estado="SP",
            setor="Varejo",
            tamanho="Pequena (1-10)",
            capital_social=50000.00,
            site="https://exemplo.com.br",
            socios=[
                Socio(nome="José da Silva", qualificacao="Sócio-Administrador"),
                Socio(nome="Maria Souza", qualificacao="Sócia"),
            ],
            contatos=[
                Contato(
                    nome="José da Silva",
                    cargo="Sócio-Administrador",
                    email="jose@exemplo.com.br",
                    telefone="(11) 1234-5678",
                    decisor=True,
                ),
            ],
        )
        repo = EmpresaRepository(session)
        repo.add(empresa)
        await session.commit()
        await session.refresh(empresa)

        assert empresa.id is not None
        assert isinstance(empresa.id, uuid.UUID)
        assert empresa.created_at is not None
        empresa_id = empresa.id

        print(f"   Empresa criada: id={empresa_id}")
        print(f"   Timestamp auto: created_at={empresa.created_at}")

    # ── 3. SELECT por CNPJ ───────────────────────────────────────
    print("\n→ Test 2: SELECT por CNPJ")
    async with get_session() as session:
        repo = EmpresaRepository(session)
        encontrada = await repo.find_by_cnpj(CNPJ_TESTE)
        assert encontrada is not None
        assert encontrada.id == empresa_id
        assert len(encontrada.socios) == 2
        assert len(encontrada.contatos) == 1
        print(f"   Encontrada: {encontrada.nome}")
        print(f"   {len(encontrada.socios)} sócios carregados (selectin)")
        print(f"   {len(encontrada.contatos)} contatos carregados")

    # ── 4. UPSERT (segundo insert atualiza em vez de duplicar) ───
    print("\n→ Test 3: UPSERT idempotente")
    async with get_session() as session:
        repo = EmpresaRepository(session)
        empresa_atualizada = Empresa(
            nome="Padaria do Teste — RENOMEADA",
            cnpj=CNPJ_TESTE,
            cidade="Rio de Janeiro",
            estado="RJ",
        )
        resultado = await repo.upsert_by_cnpj(empresa_atualizada)
        await session.commit()
        await session.refresh(resultado)

        assert resultado.id == empresa_id, "upsert NÃO deveria criar novo"
        assert resultado.nome == "Padaria do Teste — RENOMEADA"
        assert resultado.cidade == "Rio de Janeiro"
        assert resultado.razao_social == "Padaria do Teste Ltda"
        print(f"   Upsert atualizou (mesmo id={resultado.id})")
        print(f"   Nome novo: {resultado.nome}")
        print(f"   Razão social preservada: {resultado.razao_social}")

    # ── 5. CASCADE DELETE ────────────────────────────────────────
    print("\n→ Test 4: DELETE em cascata")
    async with get_session() as session:
        repo = EmpresaRepository(session)
        empresa = await repo.get_by_id(empresa_id)
        assert empresa is not None
        await session.delete(empresa)
        await session.commit()

    async with get_session() as session:
        repo = EmpresaRepository(session)
        sumiu = await repo.find_by_cnpj(CNPJ_TESTE)
        assert sumiu is None
        contato_repo = ContatoRepository(session)
        sobras = await contato_repo.list_by_empresa(empresa_id)
        assert len(sobras) == 0
        print("   Empresa removida")
        print("   Sócios e contatos removidos junto (CASCADE)")

    print("\n" + "━" * 60)
    print("TUDO OK — Passo 1 funcionando!")
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