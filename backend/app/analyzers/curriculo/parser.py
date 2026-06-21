"""Parser da resposta do gerador de currículo."""
from __future__ import annotations

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.pessoal import (
    CompetenciaGrupo,
    CurriculoExperiencia,
    CurriculoProjeto,
)
from app.utils.logger import get_logger

logger = get_logger()


class CurriculoLLM:
    """Saída crua do LLM (sem os dados factuais, que o serviço injeta)."""

    def __init__(
        self,
        titulo: str | None,
        resumo: str | None,
        competencias: list,
        experiencias: list,
        projetos: list,
    ):
        self.titulo = titulo
        self.resumo = resumo
        self.competencias = competencias
        self.experiencias = experiencias
        self.projetos = projetos


def parse_resposta(texto_cru: str) -> CurriculoLLM | None:
    dados = extrair_json(texto_cru)
    if not isinstance(dados, dict):
        return None
    try:
        competencias = [
            CompetenciaGrupo(**c)
            for c in (dados.get("competencias") or [])
            if isinstance(c, dict) and c.get("categoria") and (c.get("itens") or [])
        ]
        experiencias = [
            CurriculoExperiencia(**e)
            for e in (dados.get("experiencias") or [])
            if isinstance(e, dict)
        ]
        projetos = [
            CurriculoProjeto(**p)
            for p in (dados.get("projetos") or [])
            if isinstance(p, dict) and p.get("nome")
        ]
    except ValidationError as e:
        logger.warning("Currículo não validou: %s", e)
        return None

    return CurriculoLLM(
        titulo=dados.get("titulo"),
        resumo=dados.get("resumo"),
        competencias=competencias[:8],
        experiencias=experiencias,
        projetos=projetos[:4],
    )
