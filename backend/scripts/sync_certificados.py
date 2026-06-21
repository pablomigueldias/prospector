"""Sincroniza os certificados da pasta pública do Drive com o Perfil Mestre.

Baixa cada PDF, extrai os campos via Gemini multimodal e faz merge idempotente
(chave = nome do arquivo). Rodar de novo só pega arquivos novos.

Uso:
    python backend/scripts/sync_certificados.py            # incremental
    python backend/scripts/sync_certificados.py --reset    # zera a lista antes
                                                           # (troca placeholders
                                                           #  do seed pelos reais)
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import argparse
import asyncio

from app.api.schemas.pessoal import PerfilMestreUpsert
from app.api.services.pessoal import certificado_sync_service
from app.api.services.pessoal.perfil_service import get_perfil, salvar_perfil


async def _reset_certificacoes() -> None:
    perfil = await get_perfil()
    if perfil is None:
        print("✗ Sem Perfil Mestre ativo.")
        sys.exit(1)
    payload = PerfilMestreUpsert(
        **perfil.model_dump(exclude={"id", "ativo", "created_at",
                                     "updated_at", "certificacoes"}),
        certificacoes=[],
    )
    await salvar_perfil(payload)
    print("• Certificações zeradas (vão ser repopuladas pelo scan).")


async def main(reset: bool) -> None:
    if reset:
        await _reset_certificacoes()

    print("• Sincronizando com o Drive (baixa + extrai via Gemini)…")
    res = await certificado_sync_service.sincronizar()

    print(f"\nNa pasta: {res.total_na_pasta} | novos: {res.novos} | "
          f"já existiam: {res.ja_existiam} | falhas: {res.falhas}")
    for it in res.itens:
        marca = {"novo": "＋", "ja_existia": "·", "falha": "✗"}.get(it.status, "?")
        extra = f" → {it.nome}" if it.nome else (f" ({it.detalhe})" if it.detalhe else "")
        print(f"  {marca} {it.arquivo}{extra}")
    print(f"\n✓ Total de certificações no perfil: {res.total_no_perfil}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true",
                    help="zera as certificações antes (troca placeholders pelos reais)")
    args = ap.parse_args()
    asyncio.run(main(reset=args.reset))
