"""Recebe foto/PDF do Telegram e manda pro importador de boleto."""
from __future__ import annotations

import asyncio

from app.analyzers.boleto.extrator import BoletoSemChave
from app.analyzers.gemini.client import GeminiSemChave
from app.api.services.financas import importador_service
from app.integrations import telegram as tg

from ._base import _responder


async def _arquivo(chat_id: str, usuario_id: str, msg: dict) -> dict:
    """Baixa o arquivo do Telegram e manda pro importador de boleto."""
    if msg.get("document"):
        doc = msg["document"]
        file_id = doc["file_id"]
        nome = doc.get("file_name") or "documento"
        mime = doc.get("mime_type") or "application/pdf"
    else:  # photo: lista de tamanhos, pega o maior
        foto = msg["photo"][-1]
        file_id = foto["file_id"]
        nome, mime = "foto.jpg", "image/jpeg"

    await _responder(chat_id, "📎 Recebi, lendo o boleto...")
    caminho = await asyncio.to_thread(tg.get_file_path, file_id)
    conteudo = await asyncio.to_thread(tg.download_file, caminho)

    try:
        resp = await importador_service.importar_boleto(
            usuario_id=usuario_id, conteudo=conteudo,
            nome_original=nome, content_type=mime,
        )
    except (BoletoSemChave, GeminiSemChave):
        await _responder(
            chat_id,
            "🤖 A leitura por IA não está configurada agora (falta a chave do "
            "Gemini). Lance pelo <code>/gasto</code> por enquanto.",
        )
        return {"ok": True, "tipo": "arquivo", "erro": "sem_chave"}
    prefixo = "✅" if resp.conferido else ("⚠️" if resp.success else "❌")
    await _responder(chat_id, f"{prefixo} {resp.mensagem}")
    return {"ok": True, "tipo": "arquivo", "conferido": resp.conferido,
            "transacao_id": resp.transacao_id}
