"""Export / Backup — /api/export (S8, self-service).

Exige `usuarios.gerenciar` (admin): exportar a base inteira é sensível.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.dependencies.auth import require_permission
from app.api.services import export_service
from app.db.models.auth.usuario import Usuario

router = APIRouter(prefix="/api/export", tags=["export"])

_admin = require_permission("usuarios.gerenciar")


@router.get("/recursos", summary="Lista os recursos exportáveis")
async def recursos(_: Usuario = Depends(_admin)) -> list[str]:
    return list(export_service.RECURSOS)


@router.get("/csv/{recurso}", summary="Exporta um recurso em CSV")
async def exportar_csv(
    recurso: str,
    _: Usuario = Depends(_admin),
) -> PlainTextResponse:
    try:
        rows = await export_service.linhas(recurso)
    except export_service.ExportError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return PlainTextResponse(
        export_service.to_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{recurso}.csv"',
        },
    )


@router.get("/backup", summary="Backup JSON com todos os recursos")
async def exportar_backup(_: Usuario = Depends(_admin)) -> JSONResponse:
    return JSONResponse(
        await export_service.backup(),
        headers={
            "Content-Disposition": 'attachment; filename="backup.json"',
        },
    )
