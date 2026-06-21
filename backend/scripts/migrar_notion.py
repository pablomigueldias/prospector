"""Migra o CRM do Notion → Postgres (keystone do 'CRM fora do Notion').

Idempotente: empresas casadas por CNPJ, contatos por empresa+email/nome.
Rodar de novo só atualiza/insere o que mudou. O Notion segue intacto (a
transição é dual-write; nada é apagado lá).

Uso:
    python backend/scripts/migrar_notion.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import asyncio

from app.exporters.notion.importer import importar


async def main() -> None:
    print("• Lendo Notion (empresas + contatos) e migrando pro Postgres…")
    res = await importar()
    print(f"\n  empresas lidas:  {res.empresas_lidas}")
    print(f"  páginas ignoradas (vazias): {res.paginas_ignoradas}")
    print(f"  contatos lidos:  {res.contatos_lidos}")
    print(f"  contatos sem empresa: {res.empresas_sem_link}")
    print(f"  negócios lidos:  {res.negocios_lidos}")
    print(f"  projetos lidos:  {res.projetos_lidos}")
    print(f"  atividades lidas: {res.atividades_lidas}")
    if res.erros:
        print(f"\n  ⚠️  {len(res.erros)} erro(s):")
        for e in res.erros[:15]:
            print(f"    - {e}")
    print("\n✓ Migração concluída (Notion preservado).")


if __name__ == "__main__":
    asyncio.run(main())
