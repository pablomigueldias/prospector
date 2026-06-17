from __future__ import annotations

from app.db.sync_bridge import bridge_session
from app.mailer.outreach import gerar_followups_pendentes, gerar_rascunhos_pendentes
from app.mailer.sync import _sincronizar_async
from app.repositories.email_outreach_repository import EmailOutreachRepository


async def gerar(limit, pausa) -> dict:
    return await gerar_rascunhos_pendentes(limit=limit, pausa=pausa)

async def gerar_followups(dias, max_followups, limit, pausa) -> dict:
    return await gerar_followups_pendentes(
        dias=dias, max_followups=max_followups, limit=limit, pausa=pausa
    )

async def sincronizar_async(dias: int = 30) -> dict:
    return await _sincronizar_async(dias=dias)


def _iso(dt):
    return dt.isoformat(timespec="seconds") if dt else None


async def historico(limit: int = 50) -> list[dict]:
    async with bridge_session() as session:
        repo = EmailOutreachRepository(session)
        rows = await repo.listar_recentes(limit=limit)
        return [
            {
                "id": str(r.id),
                "destinatario": r.destinatario,
                "assunto": r.assunto,
                "tom": r.tom,
                "status": r.status,
                "follow_up_num": r.follow_up_num,
                "draft_criado_em": _iso(r.draft_criado_em),
                "enviado_em": _iso(r.enviado_em),
                "primeira_resposta_em": _iso(r.primeira_resposta_em),
            }
            for r in rows
        ]
