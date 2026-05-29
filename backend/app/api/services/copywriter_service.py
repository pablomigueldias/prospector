"""Service do Copywriter — orquestra a geração de e-mails."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.api.schemas.copywriter import CopywriterRequest, CopywriterResponse
from app.analyzers.copywriter.prompt_builder import construir_prompt
from app.analyzers.copywriter.parser import parse_resposta
from app.analyzers.llm_provider import gerar_texto
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()


class CopywriterError(Exception):
    """Erro de negócio do Copywriter — vira HTTP 400 no router."""


def _enriquecer_com_lead(req: CopywriterRequest) -> CopywriterRequest:
    """Preenche campos vazios do request com dados de um lead já coletado."""
    from app.utils.storage import load_lead  

    try:
        lead = load_lead(req.lead_arquivo)
    except FileNotFoundError:
        raise CopywriterError(
            f"Lead '{req.lead_arquivo}' não encontrado no histórico."
        )
    except Exception as e:
        raise CopywriterError(f"Falha ao ler o lead: {e}")

    def do_lead(chave: str, padrao=None):
        if isinstance(lead, dict):
            return lead.get(chave, padrao)
        return getattr(lead, chave, padrao)

    def preferir(valor_atual, valor_lead):
        return valor_atual if (valor_atual and str(valor_atual).strip()) else valor_lead

    socios = do_lead("socios") or []
    primeiro_socio = socios[0] if socios else None
    analise = do_lead("notas") or do_lead("analise_ia") or ""

    contexto_combinado = req.contexto_extra or ""
    if analise:
        contexto_combinado = (
            f"{contexto_combinado}\n\n"
            f"ANÁLISE PRÉVIA DESTE LEAD (gerada na prospecção):\n{analise}"
        ).strip()

    return req.model_copy(update={
        "empresa": preferir(req.empresa, do_lead("empresa") or do_lead("nome")),
        "segmento": preferir(req.segmento, do_lead("setor")),
        "nome_contato": preferir(req.nome_contato, primeiro_socio),
        "contexto_extra": contexto_combinado or None,
    })


def _salvar_email(req: CopywriterRequest, resp: CopywriterResponse) -> None:
    """Salva o e-mail gerado em data/emails/. Falha aqui não quebra a geração."""
    try:
        pasta = Path(settings.data_dir) / "emails"
        pasta.mkdir(parents=True, exist_ok=True)

        carimbo = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        empresa_slug = "".join(
            c for c in req.empresa.lower() if c.isalnum() or c == " "
        ).strip().replace(" ", "_")[:40]

        destino = pasta / f"{carimbo}_{empresa_slug}.json"
        destino.write_text(resp.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Copywriter: e-mail salvo em %s", destino)
    except Exception as e:
        logger.warning("Copywriter: não foi possível salvar o e-mail: %s", e)


def gerar_email(req: CopywriterRequest) -> CopywriterResponse:
    """Gera um e-mail de prospecção a partir do request."""
    if req.lead_arquivo:
        logger.info("Copywriter: enriquecendo com lead '%s'", req.lead_arquivo)
        req = _enriquecer_com_lead(req)

    if not req.empresa or not req.empresa.strip():
        raise CopywriterError("É obrigatório informar a empresa alvo.")

    prompt = construir_prompt(req)
    logger.debug("Copywriter: prompt montado (%d caracteres)", len(prompt))

    try:
        texto_cru = gerar_texto(prompt, json_mode=True,
                                agente="copywriter", operacao="gerar_email")
    except Exception as e:
        logger.error("Copywriter: falha na chamada da LLM: %s", e)
        raise CopywriterError(
            "Não foi possível contatar o modelo de IA. "
            "Verifique a conexão ou as configurações e tente de novo."
        )

    resultado = parse_resposta(texto_cru)
    if resultado is None:
        raise CopywriterError(
            "A IA não retornou um e-mail válido. Tente gerar novamente."
        )

    _salvar_email(req, resultado)
    logger.info(
        "Copywriter: e-mail gerado para '%s' (%d variantes)",
        req.empresa, len(resultado.variantes),
    )
    return resultado
