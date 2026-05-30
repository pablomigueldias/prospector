import imaplib
import smtplib
import ssl
import os
from email.message import EmailMessage
from email.utils import make_msgid

EMAIL = os.environ["MAIL_USER"]
SENHA = os.environ["MAIL_PASS"]

IMAP_HOST = "imap.hostinger.com"
SMTP_HOST = "smtp.hostinger.com"

print("teste lendo a caixa...")
imap = imaplib.IMAP4_SSL(IMAP_HOST, 993)
imap.login(EMAIL, SENHA)
print("Login IMAP OK")

print("\n2. Pastas disponíveis na sua caixa:")
status, pastas = imap.list()
for p in pastas:
    print("   ", p.decode())

print("\n3. Testando SMTP (login, sem enviar nada)...")
ctx = ssl.create_default_context()
smtp = smtplib.SMTP_SSL(SMTP_HOST, 465, context=ctx)
smtp.login(EMAIL, SENHA)
print("   ✅ Login SMTP OK")
smtp.quit()

print("\n4. Testando salvar um RASCUNHO de teste...")
PASTA_DRAFTS = "INBOX.Drafts"

msg = EmailMessage()
msg["From"] = EMAIL
msg["To"] = "ninguem@exemplo.com"
msg["Subject"] = "RASCUNHO DE TESTE"
msg["Message-ID"] = make_msgid()
msg.set_content("Teste")

resultado = imap.append(
    PASTA_DRAFTS,
    "(\\Draft)",
    None,
    msg.as_bytes(),
)
print(f"   Resultado do append: {resultado}")

imap.logout()
