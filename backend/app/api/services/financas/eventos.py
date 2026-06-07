"""Eventos em tempo real do financas via Postgres LISTEN/NOTIFY → SSE.

Quando uma transação é criada, o serviço emite um pg_notify no canal
`financas_eventos`. O endpoint SSE abre uma conexão asyncpg dedicada (LISTEN
segura a conexão), escuta o canal e repassa os eventos do usuário pro browser.
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()

CANAL = "financas_eventos"
HEARTBEAT_S = 20.0


async def notificar(session: AsyncSession, usuario_id, evento: str) -> None:
    """Emite o NOTIFY na sessão atual — entregue quando a transação commitar."""
    payload = json.dumps({"usuario_id": str(usuario_id), "evento": evento})
    await session.execute(
        text("SELECT pg_notify(:canal, :payload)"),
        {"canal": CANAL, "payload": payload},
    )


def _dsn() -> str:
    # asyncpg.connect não fala o dialeto "+asyncpg" do SQLAlchemy.
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://")


async def stream_eventos(usuario_id: str) -> AsyncIterator[str]:
    """Generator SSE: emite os eventos do canal que forem do usuario_id."""
    conn = await asyncpg.connect(_dsn())
    fila: asyncio.Queue[str] = asyncio.Queue()

    def _on_notify(_c, _pid, _channel, payload: str) -> None:
        fila.put_nowait(payload)

    await conn.add_listener(CANAL, _on_notify)
    try:
        yield ": conectado\n\n"  # abre o stream
        while True:
            try:
                payload = await asyncio.wait_for(fila.get(), timeout=HEARTBEAT_S)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"  # mantém a conexão viva
                continue
            try:
                dados = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if dados.get("usuario_id") == usuario_id:
                yield f"event: financas\ndata: {payload}\n\n"
    finally:
        try:
            await conn.remove_listener(CANAL, _on_notify)
        finally:
            await conn.close()
