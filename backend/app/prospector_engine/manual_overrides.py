from __future__ import annotations

import re

from app.collectors.website.extractors import formatar_telefone
from app.domain.lead import Contato, Lead
from app.utils.logger import get_logger

logger = get_logger()


def aplicar_overrides_manuais(
    lead: Lead,
    *,
    instagram: str | None = None,
    facebook: str | None = None,
    linkedin: str | None = None,
    email: str | None = None,
    telefone: str | None = None,
    whatsapp: str | None = None,
) -> Lead:

    aplicados: list[str] = []

    if instagram:
        url = _normalizar_instagram(instagram)
        if url:
            lead.empresa.instagram = url
            aplicados.append(f"📷 Instagram (empresa) → {url}")
        else:
            logger.warning(f"⚠️  Instagram inválido, ignorado: {instagram!r}")

    if facebook:
        url = _normalizar_facebook(facebook)
        if url:
            lead.empresa.facebook = url
            aplicados.append(f"📘 Facebook (empresa) → {url}")
        else:
            logger.warning(f"⚠️  Facebook inválido, ignorado: {facebook!r}")

    tem_dados_de_contato = any([linkedin, email, telefone, whatsapp])
    if tem_dados_de_contato:
        contato = _obter_ou_criar_contato_principal(lead)

        if linkedin:
            url = _normalizar_linkedin(linkedin)
            if url:
                contato.linkedin = url
                aplicados.append(f"💼 LinkedIn (contato) → {url}")
            else:
                logger.warning(f"⚠️  LinkedIn inválido, ignorado: {linkedin!r}")

        if email:
            email_limpo = email.strip().lower()
            if "@" in email_limpo and "." in email_limpo.split("@")[-1]:
                contato.email = email_limpo
                aplicados.append(f"📧 Email (contato) → {email_limpo}")
            else:
                logger.warning(f"⚠️  Email inválido, ignorado: {email!r}")

        if telefone:
            tel_norm = _normalizar_telefone(telefone)
            contato.telefone = tel_norm
            aplicados.append(f"☎️  Telefone (contato) → {tel_norm}")

        if whatsapp:
            whats_norm = _normalizar_telefone(whatsapp)
            contato.whatsapp = whats_norm
            aplicados.append(f"📱 WhatsApp (contato) → {whats_norm}")

        contato.origem_contato = "Network"

    if aplicados:
        logger.info("✏️  Overrides manuais aplicados:")
        for linha in aplicados:
            logger.info(f"   {linha}")
    else:
        logger.debug("ℹ️  Nenhum override manual a aplicar.")

    return lead


def _obter_ou_criar_contato_principal(lead: Lead) -> Contato:

    if lead.contatos:
        return lead.contatos[0]

    novo = Contato(
        nome=f"{lead.empresa.nome} - Contato Comercial",
        cargo="Contato comercial",
        decisor=False,
        origem_contato="Network",
    )
    lead.contatos.append(novo)
    logger.info(f"   ➕ Contato criado pra receber inputs manuais: {novo.nome!r}")
    return novo


def _normalizar_instagram(valor: str) -> str | None:

    if not valor:
        return None
    valor = valor.strip()

    if "instagram.com" in valor.lower():
        match = re.search(r"instagram\.com/([A-Za-z0-9_\.]+)", valor, re.IGNORECASE)
        if match:
            return f"https://instagram.com/{match.group(1)}"
        return None

    handle = valor.lstrip("@").strip("/")
    if not re.match(r"^[A-Za-z0-9_\.]+$", handle):
        return None
    return f"https://instagram.com/{handle}"


def _normalizar_facebook(valor: str) -> str | None:
    if not valor:
        return None
    valor = valor.strip()

    if "facebook.com" in valor.lower():
        match = re.search(
            r"facebook\.com/([A-Za-z0-9\.\-]+)",
            valor,
            re.IGNORECASE,
        )
        if match:
            return f"https://facebook.com/{match.group(1)}"
        return None

    handle = valor.lstrip("@").strip("/")
    if not re.match(r"^[A-Za-z0-9_\.\-]+$", handle):
        return None
    return f"https://facebook.com/{handle}"


def _normalizar_linkedin(valor: str) -> str | None:
    if not valor:
        return None
    valor = valor.strip()

    if "linkedin.com" in valor.lower():
        match = re.search(
            r"linkedin\.com/(company|in|school)/([A-Za-z0-9\-_\.]+)",
            valor,
            re.IGNORECASE,
        )
        if match:
            tipo = match.group(1).lower()
            slug = match.group(2)
            return f"https://linkedin.com/{tipo}/{slug}"
        return None

    slug = valor.lstrip("@").strip("/")
    if not re.match(r"^[A-Za-z0-9\-_\.]+$", slug):
        return None
    return f"https://linkedin.com/in/{slug}"


def _normalizar_telefone(valor: str) -> str:
    if not valor:
        return valor

    digitos = re.sub(r"\D", "", valor)

    if digitos.startswith("55") and len(digitos) in (12, 13):
        digitos = digitos[2:]

    if len(digitos) in (10, 11):
        return formatar_telefone(digitos)

    return valor.strip()
