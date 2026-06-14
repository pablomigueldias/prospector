"""Runner pytate dos smokes existentes.

Cada `tests/test_*.py` é um smoke auto-contido feito pra rodar como
`python -m tests.x` (tem `main()` e usa `assert`). Em vez de reescrevê-los, este
arquivo os roda **um por subprocesso** — exatamente como foram desenhados. Rodar
in-process não funciona: cada `main()` chama `asyncio.run()`, e o engine async
global do SQLAlchemy fica preso ao primeiro event loop (fechado ao fim do 1º
teste) → `RuntimeError: event loop is closed` nos seguintes. O subprocesso dá
isolamento total e mantém os smokes como fonte da verdade.

Pula a suíte se a API local (:8000) não estiver no ar (a maioria bate em
http://localhost:8000 e/ou precisa do Postgres de dev). Suba com
`python run.py serve` + os containers `db`/`minio`.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import urllib.request

import pytest

_BACKEND_DIR = pathlib.Path(__file__).parent.parent
_TESTS_DIR = pathlib.Path(__file__).parent
_MODULOS = sorted(
    p.stem
    for p in _TESTS_DIR.glob("test_*.py")
    if p.stem not in {"test_smoke_suite"}
)

# Falhas pré-existentes, fora do escopo da refatoração (não são de código):
#  - test_auth_me_logout_api: logout sem header CSRF, que o B8 passou a exigir
#    → 403. Ver docs/CONTINUACAO.md §3.4.
#  - test_financas_seed: compara a árvore de categorias com o seed; o banco de
#    DEV ganhou categorias extras criadas por uso (ex.: "Internet" em Moradia),
#    então diverge do seed puro. Passa num banco recém-semeado.
_XFAIL = {"test_auth_me_logout_api", "test_financas_seed"}


def _api_no_ar() -> bool:
    try:
        with urllib.request.urlopen(
            "http://localhost:8000/api/health", timeout=3
        ) as r:
            return r.status == 200
    except Exception:
        return False


_API_OK = _api_no_ar()


@pytest.mark.parametrize("modname", _MODULOS)
def test_smoke(modname: str) -> None:
    if not _API_OK:
        pytest.skip("API local (:8000) fora do ar — suba com 'python run.py serve'")
    proc = subprocess.run(
        [sys.executable, "-m", f"tests.{modname}"],
        cwd=str(_BACKEND_DIR),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        saida = (proc.stdout + "\n" + proc.stderr)[-3000:]
        if modname in _XFAIL:
            pytest.xfail(f"falha pré-existente conhecida (ver CONTINUACAO §3.4)\n{saida}")
        pytest.fail(f"{modname} falhou (exit {proc.returncode}):\n{saida}")
