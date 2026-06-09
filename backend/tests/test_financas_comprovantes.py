from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import text

from app.api.services.financas import comprovante_service
from app.db.session import dispose_engine, get_session
from app.utils.s3_storage import get_storage


async def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 14 (comprovantes no MinIO)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    storage = get_storage()
    criados: list[tuple[str, str]] = []  # (bucket, key)

    try:
        conteudo = b"%PDF-1.4 boleto condominio Lello junho 2026 ..."

        # ── 1. Upload de um boleto ────────────────────────────────────
        print("\n→ Test 1: upload boleto → MinIO + registro")
        comp = await comprovante_service.salvar_comprovante(
            usuario_id=usuario_id, tipo="boleto", conteudo=conteudo,
            nome_original="condominio.pdf", content_type="application/pdf",
        )
        assert comp.tipo == "boleto"
        assert comp.bucket == "boletos"
        assert comp.tamanho == len(conteudo)
        assert comp.arquivo_path.endswith(".pdf")
        criados.append((comp.bucket, comp.arquivo_path))
        print(f"   {comp.bucket}/{comp.arquivo_path} ({comp.tamanho} bytes)")

        # ── 2. Objeto está mesmo no MinIO (lê de volta) ──────────────
        print("\n→ Test 2: objeto presente no MinIO")
        obj = storage.client.get_object(Bucket=comp.bucket, Key=comp.arquivo_path)
        assert obj["Body"].read() == conteudo
        print("   conteúdo confere")

        # ── 3. Dedup: subir o mesmo arquivo devolve o mesmo registro ─
        print("\n→ Test 3: dedup por hash")
        comp2 = await comprovante_service.salvar_comprovante(
            usuario_id=usuario_id, tipo="boleto", conteudo=conteudo,
            nome_original="condominio.pdf", content_type="application/pdf",
        )
        assert comp2.id == comp.id, (comp2.id, comp.id)
        async with get_session() as session:
            n = await session.scalar(
                text("SELECT count(*) FROM financas.comprovantes WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )
        assert n == 1, f"esperava 1 registro, achei {n}"
        print("   mesmo id, sem duplicar")

        # ── 4. Tipo escolhe o bucket ──────────────────────────────────
        print("\n→ Test 4: nota_fiscal vai pro bucket 'notas'")
        nota = await comprovante_service.salvar_comprovante(
            usuario_id=usuario_id, tipo="nota_fiscal", conteudo=b"nota xyz",
            nome_original="nota.xml",
        )
        assert nota.bucket == "notas"
        criados.append((nota.bucket, nota.arquivo_path))
        print(f"   {nota.bucket}/{nota.arquivo_path}")

        # ── 5. Tipo inválido → erro ───────────────────────────────────
        print("\n→ Test 5: tipo inválido")
        try:
            await comprovante_service.salvar_comprovante(
                usuario_id=usuario_id, tipo="selfie", conteudo=b"x",
            )
            raise AssertionError("deveria ter barrado")
        except comprovante_service.ComprovanteError as e:
            print(f"   barrou: {e}")

    finally:
        # limpa MinIO e banco
        for bucket, key in criados:
            try:
                storage.client.delete_object(Bucket=bucket, Key=key)
            except Exception:
                pass
        async with get_session() as session:
            await session.execute(
                text("DELETE FROM financas.comprovantes WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )
            await session.commit()
        await dispose_engine()

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 14 funcionando!")
    print("━" * 60)


def main() -> None:
    asyncio.run(smoke_test())


if __name__ == "__main__":
    main()
