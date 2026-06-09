"""Cliente HTTP do Telegram (saída). Funções síncronas; o bot async chama via
asyncio.to_thread. Isoladas aqui pra serem mockadas nos testes."""
from __future__ import annotations

from typing import Optional

import httpx

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()

API = "https://api.telegram.org"
TIMEOUT = 20.0


def _url(metodo: str) -> str:
    return f"{API}/bot{settings.telegram_bot_token}/{metodo}"


def send_message(chat_id: str, text: str, reply_markup: Optional[dict] = None) -> dict:
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(_url("sendMessage"), json=payload)
        resp.raise_for_status()
        return resp.json()


def answer_callback_query(callback_query_id: str, text: Optional[str] = None) -> dict:
    payload: dict = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(_url("answerCallbackQuery"), json=payload)
        resp.raise_for_status()
        return resp.json()


def get_file_path(file_id: str) -> str:
    """Resolve o caminho de um arquivo enviado no chat (pra baixar)."""
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(_url("getFile"), json={"file_id": file_id})
        resp.raise_for_status()
        return resp.json()["result"]["file_path"]


def download_file(file_path: str) -> bytes:
    url = f"{API}/file/bot{settings.telegram_bot_token}/{file_path}"
    with httpx.Client(timeout=60.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content
