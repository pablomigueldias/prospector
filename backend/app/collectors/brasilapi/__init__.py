from typing import Optional

from app.collectors.brasilapi.client import (
    BrasilAPIError,
    BrasilAPIIndisponivel,
    CNPJInvalido,
    CNPJNaoEncontrado,
    buscar_cnpj,
)
from app.collectors.brasilapi.mappers import map_to_lead
from app.models.lead import Lead
from app.utils.logger import get_logger
from app.utils.storage import save_lead


logger = get_logger()

def buscar_lead_por_cnpj(cnpj: str, salvar_raw: bool = True) -> Optional[Lead]:
   
    try:
        data = buscar_cnpj(cnpj)
    except CNPJInvalido as e:
        logger.error(f"❌ CNPJ inválido: {e}")
        return None
    except CNPJNaoEncontrado:
        logger.warning(f"⚠️  CNPJ {cnpj} não encontrado na Receita")
        return None

    lead = map_to_lead(data)
    logger.success(
        f"✅ Lead montado: {lead.empresa.nome} "
        f"({len(lead.contatos)} contato(s))"
    )

    if salvar_raw:
        save_lead(lead, stage="raw")

    return lead


__all__ = [
    "buscar_lead_por_cnpj",
    "buscar_cnpj",
    "map_to_lead",
    "BrasilAPIError",
    "BrasilAPIIndisponivel",
    "CNPJInvalido",
    "CNPJNaoEncontrado",
]
