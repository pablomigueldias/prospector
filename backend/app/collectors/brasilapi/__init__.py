"""
Orquestrador multi-fonte de consulta CNPJ.

Estratégia: BrasilAPI primeiro (formato nativo, mais campos), com fallback
automático pra OpenCNPJ quando a BrasilAPI dá 404 ou está indisponível.
OpenCNPJ tem base independente da Receita, então cobre CNPJs que a BrasilAPI
não tem no cache dela.

A função pública `buscar_lead_por_cnpj` mantém a mesma assinatura de antes —
nenhum chamador precisa mudar.
"""

from typing import Any, Dict, Optional, Tuple

from app.collectors.brasilapi.client import (
    BrasilAPIError,
    BrasilAPIIndisponivel,
    CNPJInvalido,
    CNPJNaoEncontrado,
    _digits_only,
    _validate_cnpj_digits,
    buscar_cnpj,
)
from app.collectors.brasilapi.mappers import map_to_lead
from app.collectors.brasilapi.normalizers import normalizar_opencnpj_para_brasilapi
from app.collectors.brasilapi.opencnpj_client import buscar_cnpj_opencnpj
from app.models.lead import Lead
from app.utils.logger import get_logger
from app.utils.storage import save_lead


logger = get_logger()


def buscar_lead_por_cnpj(cnpj: str, salvar_raw: bool = True) -> Optional[Lead]:
    """
    Consulta CNPJ em múltiplas fontes e devolve um Lead pronto, ou None.

    Ordem de tentativa:
        1. BrasilAPI (fonte primária, dados ricos)
        2. OpenCNPJ  (fallback independente, cobre buracos da BrasilAPI)

    Devolve None se:
        - CNPJ é inválido (dígitos verificadores ou formato)
        - Nenhuma das fontes encontrou
        - Todas as fontes estão indisponíveis
    """
    digits = _digits_only(cnpj)
    if not _validate_cnpj_digits(digits):
        logger.error(f"❌ CNPJ inválido (DV): {cnpj}")
        return None

    data, fonte = _consultar_com_fallback(digits)
    if data is None:
        return None

    lead = map_to_lead(data)

    # Se veio da OpenCNPJ, anexa os extras (email/telefones) nas Notas.
    # Esses dados não existem na BrasilAPI; geralmente o email é do contador
    # (cadastro Receita), por isso vai pras Notas pro Pablo avaliar.
    extras = data.get("_extras_opencnpj") or {}
    if fonte == "opencnpj" and extras:
        _anexar_extras_nas_notas(lead, extras)

    logger.success(
        f"✅ Lead montado via {fonte.upper()}: {lead.empresa.nome} "
        f"({len(lead.contatos)} contato(s))"
    )

    if salvar_raw:
        save_lead(lead, stage="raw")

    return lead


# ─────────────────────────────────────────────────────────────────────
# Internals
# ─────────────────────────────────────────────────────────────────────


def _consultar_com_fallback(
    cnpj_digits: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Tenta BrasilAPI → OpenCNPJ na sequência.
    Devolve (dados_no_formato_brasilapi, nome_da_fonte) ou (None, None).
    """
    # ── Fonte 1: BrasilAPI ──────────────────────────────────────────
    try:
        data = buscar_cnpj(cnpj_digits)
        return data, "brasilapi"
    except CNPJInvalido as e:
        # CNPJ inválido pela API → não adianta tentar outra fonte
        logger.error(f"❌ BrasilAPI rejeitou CNPJ: {e}")
        return None, None
    except CNPJNaoEncontrado:
        logger.info(
            f"⚠️  CNPJ {cnpj_digits} não está na BrasilAPI — "
            f"tentando OpenCNPJ..."
        )
    except BrasilAPIIndisponivel as e:
        logger.warning(
            f"⚠️  BrasilAPI indisponível ({e}) — tentando OpenCNPJ..."
        )
    except BrasilAPIError as e:
        logger.warning(
            f"⚠️  Erro inesperado na BrasilAPI ({e}) — tentando OpenCNPJ..."
        )

    # ── Fonte 2: OpenCNPJ (fallback) ────────────────────────────────
    try:
        raw = buscar_cnpj_opencnpj(cnpj_digits)
        normalizado = normalizar_opencnpj_para_brasilapi(raw)
        return normalizado, "opencnpj"
    except CNPJNaoEncontrado:
        logger.warning(
            f"⚠️  CNPJ {cnpj_digits} também não está na OpenCNPJ — "
            f"empresa pode ter sido baixada ou ser muito recente"
        )
        return None, None
    except BrasilAPIIndisponivel as e:
        logger.error(f"❌ OpenCNPJ também indisponível: {e}")
        return None, None
    except BrasilAPIError as e:
        logger.error(f"❌ Erro inesperado na OpenCNPJ: {e}")
        return None, None


def _anexar_extras_nas_notas(lead: Lead, extras: Dict[str, Any]) -> None:
    """
    Aplica dados extras da OpenCNPJ ao Lead:

    - **Email da Receita** → vai pras Notas (geralmente é do contador,
      melhor não atribuir como contato comercial sem revisão)
    - **Telefone fixo (não-fax)** → o primeiro vai pro contato principal
      (lead.contatos[0]) se ainda não tiver telefone. Útil quando o
      site scraper falha (ex: SPAs sem texto) — pelo menos o telefone
      cadastrado na Receita preenche o decisor principal.
    - **Telefones restantes (incluindo fax)** → vão pras Notas
    """
    blocos = []

    # ── Email da Receita (sempre pras notas) ────────────────────────
    email = extras.get("email_receita")
    if email:
        blocos.append(
            f"📧 Email cadastrado na Receita: {email}\n"
            f"   (geralmente é do contador — confirme antes de usar)"
        )

    # ── Telefones (lógica nova: 1º não-fax → contato principal) ─────
    telefones = list(extras.get("telefones") or [])
    telefone_atribuido = None

    if telefones and lead.contatos and not lead.contatos[0].telefone:
        # Encontra o primeiro telefone não-fax pra atribuir ao contato
        for i, tel in enumerate(telefones):
            if not tel.get("is_fax"):
                telefone_atribuido = tel
                lead.contatos[0].telefone = tel.get("formatado", "?")
                logger.info(
                    f"   📞 Telefone da Receita atribuído ao 1º contato "
                    f"({lead.contatos[0].nome}): {tel.get('formatado')}"
                )
                # Remove da lista que vai pras notas
                telefones.pop(i)
                break

    if telefones:
        linhas = ["📞 Telefones cadastrados na Receita:"]
        for tel in telefones:
            marca = " (FAX)" if tel.get("is_fax") else ""
            formatado = tel.get("formatado", "?")
            linhas.append(f"   • {formatado}{marca}")
        if telefone_atribuido:
            linhas.append(
                f"   (o telefone {telefone_atribuido.get('formatado')} "
                f"foi atribuído ao contato principal)"
            )
        blocos.append("\n".join(linhas))

    if not blocos:
        return

    cabecalho = "📋 Dados extras da OpenCNPJ:"
    bloco_completo = cabecalho + "\n\n" + "\n\n".join(blocos)

    if lead.empresa.notas:
        lead.empresa.notas = f"{lead.empresa.notas}\n\n{bloco_completo}"
    else:
        lead.empresa.notas = bloco_completo


__all__ = [
    "buscar_lead_por_cnpj",
    "buscar_cnpj",
    "map_to_lead",
    "BrasilAPIError",
    "BrasilAPIIndisponivel",
    "CNPJInvalido",
    "CNPJNaoEncontrado",
]
