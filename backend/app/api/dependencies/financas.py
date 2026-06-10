"""Dependencies de autorização do módulo financeiro.

O ``usuario_id`` dos dados do financas passou a ser derivado **da sessão**
(não mais de query string / corpo da requisição). Antes, qualquer um logado
podia trocar o parâmetro e ler/gravar dados de outro perfil; agora o dono é
sempre quem está autenticado.

Camadas (todas exigem login via ``usuario_atual``):
- ``usuario_financas``  → login + permissão ``financas.ver`` (leitura).
- ``financas_usuario_id`` → o ``str(usuario.id)`` do logado (para os handlers).
- ``exige_editar``     → login + permissão ``financas.editar`` (mutações).

O caminho do **bot do Telegram** não passa por aqui (chama os services direto,
com o ``usuario_id`` do mapa de chat) — não é afetado.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException

from app.api.dependencies.auth import usuario_atual
from app.api.services.auth import permissoes as permissoes_service
from app.db.models.auth.usuario import Usuario
from app.db.session import get_session


async def _tem_permissao(usuario: Usuario, codigo: str) -> bool:
    async with get_session() as session:
        codigos = await permissoes_service.listar_codigos(session, usuario.id)
    return codigo in codigos


async def usuario_financas(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    """Login + ``financas.ver``. Base das rotas de leitura do financas."""
    if not await _tem_permissao(usuario, "financas.ver"):
        raise HTTPException(status_code=403, detail="Permissão negada.")
    return usuario


async def financas_usuario_id(
    usuario: Usuario = Depends(usuario_financas),
) -> str:
    """O perfil dono dos dados é sempre o usuário logado (nunca a query)."""
    return str(usuario.id)


async def exige_editar(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    """Login + ``financas.editar``. Use em POST/PATCH/DELETE do financas."""
    if not await _tem_permissao(usuario, "financas.editar"):
        raise HTTPException(status_code=403, detail="Permissão negada.")
    return usuario
