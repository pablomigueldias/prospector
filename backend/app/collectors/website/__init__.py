from typing import Dict, List, Optional

from app.collectors.website.crawler import coletar_do_site
from app.collectors.website.extractors import formatar_telefone, normalizar_url
from app.models.lead import Contato, Empresa, Lead
from app.utils.logger import get_logger

DDD_POR_ESTADO = {
    "SP": {"11", "12", "13", "14", "15", "16", "17", "18", "19"},
    "RJ": {"21", "22", "24"},
    "ES": {"27", "28"},
    "MG": {"31", "32", "33", "34", "35", "37", "38"},
    "PR": {"41", "42", "43", "44", "45", "46"},
    "SC": {"47", "48", "49"},
    "RS": {"51", "53", "54", "55"},
    "DF": {"61"},
    "GO": {"62", "64"},
    "TO": {"63"},
    "MT": {"65", "66"},
    "MS": {"67"},
    "AC": {"68"},
    "RO": {"69"},
    "BA": {"71", "73", "74", "75", "77"},
    "SE": {"79"},
    "PE": {"81", "87"},
    "AL": {"82"},
    "PB": {"83"},
    "RN": {"84"},
    "CE": {"85", "88"},
    "PI": {"86", "89"},
    "PA": {"91", "93", "94"},
    "AM": {"92", "97"},
    "RR": {"95"},
    "AP": {"96"},
    "MA": {"98", "99"},
}

logger = get_logger()


def _ordenar_por_ddd(numeros,estado):
    if not estado:
        return numeros
    ddds_esperados = DDD_POR_ESTADO.get(estado.upper())
    if not ddds_esperados:
        return numeros
    
    da_regiao = [n for n in numeros if n[:2] in ddds_esperados]
    de_fora = [n for n in numeros if n[:2] not in ddds_esperados]
    return da_regiao + de_fora

def enriquecer_lead_com_site(
    lead: Lead, url_site: str, salvar_url_na_empresa: bool = True
) -> Lead:

    url_norm = normalizar_url(url_site)
    contatos = coletar_do_site(url_norm)

    _aplicar_na_empresa(lead.empresa, contatos,
                        url_norm, salvar_url_na_empresa)
    _aplicar_nos_contatos(lead, contatos)
    _adicionar_extras_nas_notas(lead.empresa, contatos)

    return lead


def _aplicar_na_empresa(
    empresa: Empresa,
    contatos: Dict[str, object],
    url_site: str,
    salvar_url: bool,
) -> None:

    if salvar_url and not empresa.site:
        empresa.site = url_site

    if not empresa.instagram and contatos.get("instagram"):
        empresa.instagram = contatos["instagram"]  # type: ignore

    if not empresa.facebook and contatos.get("facebook"):
        empresa.facebook = contatos["facebook"]  # type: ignore


def _aplicar_nos_contatos(lead: Lead, contatos: Dict[str, object]) -> None:

    emails: List[str] = contatos.get("emails", [])  # type: ignore
    whatsapps: List[str] = contatos.get("whatsapps", [])  # type: ignore
    telefones: List[str] = contatos.get("telefones", [])  # type: ignore
    linkedin: Optional[str] = contatos.get("linkedin")  # type: ignore

    estado = lead.empresa.estado
    whatsapps = _ordenar_por_ddd(whatsapps, estado)
    telefones = _ordenar_por_ddd(telefones, estado)

    email_principal = emails[0] if emails else None
    whatsapp_principal = (
        formatar_telefone(whatsapps[0]) if whatsapps else None
    )
    telefone_principal = (
        formatar_telefone(telefones[0]) if telefones else None
    )

    if lead.contatos:
        principal = lead.contatos[0]
        if not principal.email and email_principal:
            principal.email = email_principal
        if not principal.whatsapp and whatsapp_principal:
            principal.whatsapp = whatsapp_principal
        if not principal.telefone and telefone_principal:
            principal.telefone = telefone_principal
        if not principal.linkedin and linkedin:
            principal.linkedin = linkedin
    else:
        if email_principal or whatsapp_principal or telefone_principal:
            nome_contato = f"{lead.empresa.nome} - Contato Comercial"
            lead.contatos.append(
                Contato(
                    nome=nome_contato,
                    cargo="Contato comercial",
                    decisor=False,
                    email=email_principal,
                    whatsapp=whatsapp_principal,
                    telefone=telefone_principal,
                    linkedin=linkedin,
                    origem_contato="Site",
                )
            )
            logger.info(f"   ➕ Criado contato genérico: {nome_contato}")


def _adicionar_extras_nas_notas(
    empresa: Empresa, contatos: Dict[str, object]
) -> None:

    extras: List[str] = []

    emails: List[str] = contatos.get("emails", [])  # type: ignore
    if len(emails) > 1:
        extras.append(f"📧 Outros emails encontrados: {', '.join(emails[1:5])}")

    whatsapps: List[str] = contatos.get("whatsapps", [])  # type: ignore
    if len(whatsapps) > 1:
        formatados = [formatar_telefone(w) for w in whatsapps[1:4]]
        extras.append(f"📱 Outros WhatsApps: {', '.join(formatados)}")

    telefones: List[str] = contatos.get("telefones", [])  # type: ignore
    if len(telefones) > 1:
        formatados = [formatar_telefone(t) for t in telefones[1:4]]
        extras.append(f"☎️  Outros telefones: {', '.join(formatados)}")

    linkedin = contatos.get("linkedin")
    if linkedin and not any("linkedin" in (c.linkedin or "") for c in []):
        pass

    if extras:
        bloco = "\n".join(extras)
        if empresa.notas:
            empresa.notas = f"{empresa.notas}\n\n{bloco}"
        else:
            empresa.notas = bloco


__all__ = ["enriquecer_lead_com_site", "coletar_do_site"]
