"""Ferramentas de DEV — rotas perigosas, habilitadas só fora de produção.

Toda rota aqui exige ``settings.dev_tools_enabled`` (env DEV_TOOLS_ENABLED=true,
que só existe no .env de dev). Em produção o flag é falso → 404, como se a rota
não existisse. Também exige login.
"""
from __future__ import annotations

import asyncio
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.dependencies.auth import usuario_atual
from app.api.services.auth import senha_service
from app.config import BASE_DIR, settings
from app.db.models.auth.usuario import Usuario
from app.db.session import dispose_engine, get_session
from app.jobs.seed_admin import ADMIN_ID
from app.utils.logger import get_logger

logger = get_logger()

router = APIRouter(prefix="/api/dev", tags=["dev"])

_SCRIPT = BASE_DIR.parent / "deploy" / "scripts" / "sync-prod-to-dev.sh"


async def _resetar_senha_admin_dev() -> str | None:
    """Depois do sync, ``auth.usuarios`` veio da PRODUÇÃO — ou seja, a senha do
    admin no dev virou a de produção. Pra você continuar logando com a senha
    LOCAL de sempre, sobrescreve o hash do admin com a ``ADMIN_SENHA_INICIAL``
    do ``.env`` de dev. Roda DEPOIS do ``dispose_engine`` (banco já recriado).
    Retorna o email resetado, ou ``None`` se não deu pra resetar."""
    if not settings.admin_email or not settings.admin_senha_inicial:
        return None
    email_norm = settings.admin_email.strip().lower()
    async with get_session() as session:
        admin = await session.get(Usuario, ADMIN_ID)
        if admin is None:
            admin = await session.scalar(
                select(Usuario).where(Usuario.email == email_norm)
            )
        if admin is None:
            return None
        admin.senha_hash = senha_service.hash_senha(settings.admin_senha_inicial)
        await session.commit()
        return admin.email


def _exige_dev() -> None:
    """Barra a rota se as ferramentas de dev não estiverem habilitadas."""
    if not settings.dev_tools_enabled:
        # 404 (não 403): não revela que a rota existe em produção.
        raise HTTPException(status_code=404, detail="Not Found")


@router.get("/status", summary="Ferramentas de dev estão habilitadas?")
async def status() -> dict:
    return {"dev_tools_enabled": settings.dev_tools_enabled}


@router.post("/sync-prod-to-dev",
             summary="Copia os dados da produção para o banco de dev (DESTRUTIVO)")
async def sync_prod_to_dev(_: Usuario = Depends(usuario_atual)) -> dict:
    _exige_dev()
    if not _SCRIPT.exists():
        raise HTTPException(status_code=500, detail=f"Script não encontrado: {_SCRIPT}")

    env = {**os.environ, "ASSUME_YES": "1"}
    logger.info("Sync produção→dev iniciado via dashboard.")
    try:
        proc = await asyncio.create_subprocess_exec(
            "bash", str(_SCRIPT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )
        out, _err = await asyncio.wait_for(proc.communicate(), timeout=300)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Sync demorou demais (timeout 5min).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao rodar o sync: {e}")

    log = (out or b"").decode("utf-8", "replace")
    if proc.returncode != 0:
        logger.error("Sync produção→dev falhou (rc=%s):\n%s", proc.returncode, log)
        raise HTTPException(
            status_code=500,
            detail=f"Sync falhou (rc={proc.returncode}). {log.strip()[-400:]}",
        )

    # O banco de dev foi recriado: descarta o pool pra reconectar no novo banco.
    await dispose_engine()
    logger.info("Sync produção→dev concluído; engine descartado.")

    # O dump trouxe a senha de PRODUÇÃO; devolve a senha LOCAL de dev pro admin
    # pra você não precisar lembrar a senha do site toda vez que sincroniza.
    try:
        email = await _resetar_senha_admin_dev()
    except Exception as e:  # nunca falha o sync por causa do reset
        logger.error("Reset de senha pós-sync falhou: %s", e)
        email = None

    if email:
        msg = (
            "Dados da produção copiados para o dev. Faça login de novo com sua "
            "senha LOCAL de dev (a do .env). Recarregando…"
        )
    else:
        msg = (
            "Dados da produção copiados para o dev. Login = senha da PRODUÇÃO "
            "(não consegui resetar pra senha local). Recarregue a página."
        )
    return {
        "ok": True,
        "mensagem": msg,
        "senha_resetada": bool(email),
        "log": log.strip()[-2000:],
    }
