"""Parser da resposta do extrator de certificado."""
from __future__ import annotations

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.pessoal import CertificadoExtraido
from app.utils.logger import get_logger

logger = get_logger()


def parse_certificado(texto_cru: str) -> CertificadoExtraido | None:
    """Converte o texto cru da LLM num CertificadoExtraido validado, ou None."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None
    try:
        return CertificadoExtraido(**dados)
    except ValidationError as e:
        logger.warning("Certificado extraído não passou na validação: %s", e)
        return None
