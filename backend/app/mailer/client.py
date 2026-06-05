from __future__ import annotations

import imaplib
import re
import email
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Optional,List,Dict,Any

from app.config import settings
from app.utils.logger import get_logger


logger = get_logger()


class MailerError(Exception):
    """Erro genérico"""


def _conectar_imap() -> imaplib.IMAP4_SSL:
    if not settings.mail_user or not settings.mail_password:
        raise MailerError("MAIL_USER / MAIL_PASS NÃO ESTÃO NO .env")
    imap = imaplib.IMAP4_SSL(settings.mail_imap_host, settings.mail_imap_port)
    imap.login(settings.mail_user, settings.mail_password)
    return imap


def _achar_pasta(imap: imaplib.IMAP4_SSL, tipo: str) -> str:

    flag_alvo = f"\\{tipo}".lower()
    nomes_provaveis = {
        "Drafts": {"drafts", "rascunhos", "inbox.drafts"},
        "Sent": {"sent", "enviados", "inbox.sent", "sent items"},
    }[tipo]

    status, linhas = imap.list()
    if status != "OK":
        raise MailerError("Não consegui listar as pastas do IMAP")

    padrao = re.compile(
        r'\((?P<flags>[^)]*)\)\s+(?:"[^"]*"|NIL)\s+(?P<name>.+)$')
    fallback: Optional[str] = None

    for raw in linhas:
        linha = raw.decode(errors="ignore").strip()
        m = padrao.match(linha)
        if m:
            flags = m.group("flags").lower()
            nome = m.group("name").strip().strip('"')
        else:
            flags = linha.lower()
            partes = linha.split()
            nome = partes[-1].strip('"') if partes else ""

        if not nome:
            continue
        if flag_alvo in flags:
            return nome
        if nome.lower() in nomes_provaveis and fallback is None:
            fallback = nome

    if fallback:
        return fallback
    raise MailerError(
        f"Não achei a pasta {tipo}. Confira os nomes na lista do IMAP."
    )


def salvar_rascunho(
        *,
        para: str,
        assunto: str,
        corpo: str,
        de_nome: Optional[str] = None,
) -> str:

    de_nome = de_nome or settings.mail_from_name
    dominio = settings.mail_user.split("@")[-1]
    message_id = make_msgid(domain=dominio)

    msg = EmailMessage()
    msg["From"] = formataddr((de_nome, settings.mail_user))
    msg["To"] = para
    msg["Subject"] = assunto
    msg["Message-ID"] = message_id
    msg.set_content(corpo)

    imap = _conectar_imap()
    try:
        pasta = _achar_pasta(imap, "Drafts")
        logger.info(f"Pasta de rascunhos resolvida: {pasta!r}")
        status, dados = imap.append(pasta, "(\\Draft)", None, msg.as_bytes()) #type:ignore
        if status != "OK":
            raise MailerError(f"Append falhou em {pasta!r}: {status} {dados}")
        logger.success(f"Rascunho salvo em '{pasta}' para {para}")
        return message_id
    finally:
        imap.logout()

def _decodificar(valor: Optional[str]) -> str:
    if not valor:
        return ""
    try:
        return str(make_header(decode_header(valor)))
    except Exception:
        return valor
    
def _normalizar_assunto(assunto: str) -> str:
    s = _decodificar(assunto).strip().lower()
    while True:
        novo = re.sub(r"^(re|res|fwd|fw|enc)\s*:\s*", "", s, flags=re.IGNORECASE)
        if novo == s:
            break
        s = novo
    return s.strip()

def _ler_pasta(pasta_tipo: str, dias: int = 30) -> List[Dict[str, Any]]:
    imap = _conectar_imap()
    try:
        if pasta_tipo == "INBOX":
            pasta = "INBOX"
        else:
            pasta = _achar_pasta(imap, pasta_tipo)

        status, _ = imap.select(pasta, readonly=True)
        if status != "OK":
            raise MailerError(f"Não consegui abrir a pasta {pasta!r}")

        # Filtra por data no servidor
        from datetime import timedelta
        desde = (datetime.now() - timedelta(days=dias)).strftime("%d-%b-%Y")
        status, dados = imap.search(None, f'(SINCE {desde})')
        if status != "OK":
            return []

        ids = dados[0].split()
        mensagens: List[Dict[str, Any]] = []

        for num in ids:
            status, msg_data = imap.fetch(num, "(BODY.PEEK[])")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            mensagens.append({
                "message_id": (msg.get("Message-ID") or "").strip(),
                "in_reply_to": (msg.get("In-Reply-To") or "").strip(),
                "references": (msg.get("References") or "").strip(),
                "from": _decodificar(msg.get("From")),
                "to": _decodificar(msg.get("To")),
                "subject": _decodificar(msg.get("Subject")),
                "subject_norm": _normalizar_assunto(msg.get("Subject") or ""),
                "date": _parse_data(msg.get("Date")),
                "corpo": _remover_citacao(_extrair_corpo_texto(msg))
            })
        return mensagens
    finally:
        imap.logout()


def _parse_data(valor: Optional[str]) -> Optional[datetime]:
    if not valor:
        return None
    try:
        dt = parsedate_to_datetime(valor)
        return dt.replace(tzinfo=None) if dt and dt.tzinfo else dt
    except Exception:
        return None
    
def ler_enviados(dias: int = 30) -> List[Dict[str, Any]]:
    return _ler_pasta("Sent", dias=dias)


def ler_inbox(dias: int = 30) -> List[Dict[str, Any]]:
    return _ler_pasta("INBOX", dias=dias)

def _extrair_emails(campo: str) -> List[str]:
    return [e.lower() for e in re.findall(r"[\w\.\-\+]+@[\w\-\.]+", campo or "")]

def _extrair_corpo_texto(msg: email.message.Message) -> str:
    def _decode(part) -> str:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ""
        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except (LookupError, ValueError):
            return payload.decode("utf-8", errors="replace")

    if not msg.is_multipart():
        return _decode(msg).strip()

    texto_plano = ""
    texto_html = ""
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        disp = (part.get("Content-Disposition") or "").lower()
        if "attachment" in disp:
            continue
        ctype = part.get_content_type()
        if ctype == "text/plain" and not texto_plano:
            texto_plano = _decode(part)
        elif ctype == "text/html" and not texto_html:
            texto_html = _decode(part)

    if texto_plano.strip():
        return texto_plano.strip()
    if texto_html.strip():
        sem_tags = re.sub(r"<[^>]+>", " ", texto_html)
        sem_tags = re.sub(r"\s+", " ", sem_tags)
        return sem_tags.strip()
    return ""

def _remover_citacao(corpo: str) -> str:
    """Corta a thread citada embaixo da resposta."""
    linhas = corpo.splitlines()
    resultado = []
    for linha in linhas:
        l = linha.strip()
        if l.startswith(">"):
            break
        if re.match(r"^(Em|On)\s.+\d", l):
            break
        if re.match(r"^-{2,}\s*Mensagem original", l, re.IGNORECASE):
            break
        if re.match(r"^De:\s", l) and resultado:
            break
        resultado.append(linha)
    texto = "\n".join(resultado).strip()
    return texto if texto else corpo.strip()