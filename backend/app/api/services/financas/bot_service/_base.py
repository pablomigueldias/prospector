"""Base do bot: config (mapa chat→usuário), envio ao Telegram, textos de
ajuda e helpers puros (parse de período, heurística de prevista, teclado do
card). Sem dependência dos outros submódulos."""
from __future__ import annotations

import asyncio
from datetime import date
from typing import Optional

from app.config import settings
from app.integrations import telegram as tg
from app.utils.logger import get_logger

logger = get_logger()

AJUDA = (
    "💰 <b>Seu organizador financeiro</b> — o que dá pra fazer:\n"
    "\n"
    "💸 <b>Lançar na hora</b>\n"
    "• <code>/gasto 50 mercado</code> (saída)\n"
    "• <code>/ganho 2000 salário</code> (entrada)\n"
    "• acrescente a conta no fim: <code>/gasto 50 mercado vr</code>\n"
    "\n"
    "💬 <b>Falar normal</b> (eu monto um card pra você confirmar)\n"
    "• <i>gastei 80 no posto</i>\n"
    "• <i>recebi 2000 de salário</i>\n"
    "\n"
    "📎 <b>Boleto ou comprovante</b>\n"
    "• manda o PDF ou a foto que eu leio e lanço sozinho\n"
    "\n"
    "📊 <b>Consultar</b>\n"
    "• /saldo — saldo das suas contas\n"
    "• /resumo — receitas x despesas do mês\n"
    "• <code>/resumo julho</code> — de um mês específico\n"
    "\n"
    "🏦 <b>Contas</b>\n"
    "• /contas — listar suas contas\n"
    "• <code>/conta Nubank corrente</code> — criar uma conta\n"
    "\n"
    "↩️ <b>Errou?</b>\n"
    "• /desfazer — apaga o último lançamento\n"
    "\n"
    "ℹ️ Reveja isto quando quiser com /help."
)

BOAS_VINDAS = "👋 <b>Tudo certo, bot no ar!</b>\n\n"


def mapa_chat_usuario() -> dict[str, str]:
    """chat_id (str) → usuario_id (UUID str). Lido das settings."""
    mapa: dict[str, str] = {}
    if settings.telegram_chat_id and settings.telegram_usuario_id:
        mapa[str(settings.telegram_chat_id)] = settings.telegram_usuario_id
    if settings.telegram_chat_id_sandra and settings.telegram_usuario_id_sandra:
        mapa[str(settings.telegram_chat_id_sandra)] = settings.telegram_usuario_id_sandra
    return mapa


async def _responder(chat_id: str, texto: str, reply_markup: Optional[dict] = None) -> None:
    await asyncio.to_thread(tg.send_message, chat_id, texto, reply_markup)


def _consulta_intent(texto: str) -> Optional[str]:
    """Distingue uma PERGUNTA de um lançamento. 'gastei 50 no mercado' não é
    consulta; 'quanto gastei?' / 'qual meu saldo?' são."""
    t = texto.lower()
    if "saldo" in t:
        return "saldo"
    if any(k in t for k in ("quanto", "resumo", "sobrou", "sobra", "balanço", "balanco")):
        return "resumo"
    return None


_MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}


def _parse_periodo(arg: str) -> tuple[int, int]:
    """Texto após /resumo → (ano, mes). Aceita nome do mês (julho/jul), número
    (7), MM/AAAA (07/2025) e AAAA-MM (2025-07). Vazio = mês atual. Nome de mês
    futuro cai no ano anterior (a ocorrência mais recente daquele mês)."""
    hoje = date.today()
    a = arg.strip().lower()
    if not a:
        return hoje.year, hoje.month

    # AAAA-MM ou MM/AAAA
    for sep, ordem in (("-", "ay"), ("/", "ya")):
        if sep in a:
            p = a.split(sep)
            if len(p) == 2 and p[0].isdigit() and p[1].isdigit():
                x, y = int(p[0]), int(p[1])
                ano, mes = (x, y) if ordem == "ay" else (y, x)
                if 1 <= mes <= 12:
                    return ano, mes

    # Nome do mês
    if a in _MESES:
        mes = _MESES[a]
        ano = hoje.year if mes <= hoje.month else hoje.year - 1
        return ano, mes

    # Número do mês
    if a.isdigit() and 1 <= int(a) <= 12:
        mes = int(a)
        ano = hoje.year if mes <= hoje.month else hoje.year - 1
        return ano, mes

    return hoje.year, hoje.month


def _card_keyboard(rid: str) -> dict:
    return {"inline_keyboard": [
        [{"text": "✅ Confirmar", "callback_data": f"confirmar:{rid}"},
         {"text": "❌ Cancelar", "callback_data": f"cancelar:{rid}"}],
        [{"text": "✏️ Editar", "callback_data": f"editar:{rid}"}],
    ]}


_MARCADORES_FUTURO = (
    "vou pagar", "vou gastar", "pagar dia", "agendar", "agenda ", "agendado",
    "previst", "vence", "marcar pra", "marca pra", "tenho que pagar",
    "preciso pagar", "pagar amanhã", "pagar amanha",
)


def _eh_prevista(texto: str, data_interp: date) -> bool:
    """Heurística: frase sobre o futuro ('vou pagar', 'dia 10', 'agendar') ou
    data interpretada à frente de hoje → lança como prevista (não move saldo)."""
    if data_interp and data_interp > date.today():
        return True
    t = texto.lower()
    return any(m in t for m in _MARCADORES_FUTURO)
