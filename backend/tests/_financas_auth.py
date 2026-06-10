"""Helper para os smoke tests do financas após o endurecimento do `usuario_id`.

As rotas `/api/financas/*` passaram a derivar o dono dos dados da **sessão**
(ver `app/api/dependencies/financas.py`), exigindo login + permissão. Para os
smoke tests continuarem leves (sem subir o fluxo de login/CSRF em cada um),
sobrescrevemos as dependencies de auth via `app.dependency_overrides`,
fixando o `usuario_id` que o teste quer usar.

O fluxo end-to-end real (cookie, 401, body forjado ignorado, 403 sem
permissão) é coberto à parte em `tests/test_financas_auth_api.py`.

Uso:
    from tests._financas_auth import usar_usuario, limpar_override
    usar_usuario(meu_uid)        # rotas tratam meu_uid como o logado
    ...                          # roda o teste normalmente
    limpar_override()            # no finally
"""
from __future__ import annotations

from app.api.dependencies import financas as _dep
from app.api.main import app


def usar_usuario(usuario_id: str) -> None:
    """Faz as rotas de financas tratarem ``usuario_id`` como o usuário logado."""
    app.dependency_overrides[_dep.financas_usuario_id] = lambda: usuario_id
    app.dependency_overrides[_dep.usuario_financas] = lambda: None
    app.dependency_overrides[_dep.exige_editar] = lambda: None


def limpar_override() -> None:
    for dep in (_dep.financas_usuario_id, _dep.usuario_financas, _dep.exige_editar):
        app.dependency_overrides.pop(dep, None)
