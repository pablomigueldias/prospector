from typing import Optional

from app.analyzers.gemini.client import (
    GeminiError,
    GeminiSemChave,
)
from app.analyzers.gemini.parser import AnaliseGemini, formatar_para_notas, parse_resposta
from app.analyzers.gemini.prompt_builder import construir_prompt
from app.analyzers.llm_provider import gerar_texto
from app.models.lead import Lead
from app.utils.logger import get_logger


logger = get_logger()


def analisar_lead(lead: Lead) -> Optional[AnaliseGemini]:

    prompt = construir_prompt(lead)
    logger.debug(f"Prompt ({len(prompt)} chars) montado")

    try:
        texto = gerar_texto(prompt, json_mode=True,
                            agente="prospector", operacao="analise_lead")
    except Exception as e:
        logger.error(f"Falha na análise (Gemini e fallback): {type(e).__name__}: {e}")
        return None

    analise = parse_resposta(texto)
    if analise is None:
        logger.error("Não foi possível parsear a resposta da IA")
        return None

    logger.success(f"Análise gerada: score {analise.score}/100")
    return analise


def enriquecer_lead_com_analise(lead: Lead) -> Lead:

    analise = analisar_lead(lead)
    if analise is None:
        logger.warning("Lead segue sem análise da IA (vide logs)")
        return lead

    lead.empresa.score = analise.score
    lead.empresa.score = analise.score
    lead.empresa.analise_json = {
        "dores": [d.model_dump() for d in analise.dores_provaveis],
        "ganchos": [g.model_dump() for g in analise.ganchos_venda],
    }

    bloco_ia = formatar_para_notas(analise)
    if lead.empresa.notas:
        lead.empresa.notas = f"{lead.empresa.notas}\n\n{bloco_ia}"
    else:
        lead.empresa.notas = bloco_ia

    return lead


__all__ = [
    "analisar_lead",
    "enriquecer_lead_com_analise",
    "AnaliseGemini",
    "formatar_para_notas",
    "construir_prompt",
    "GeminiError",
    "GeminiSemChave",
]
