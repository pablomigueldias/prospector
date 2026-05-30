import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import argparse

from app.api.schemas.copywriter import CopywriterRequest
from app.api.services.copywriter_service import gerar_email, CopywriterError
from app.mailer.client import salvar_rascunho, MailerError



def main():
    p = argparse.ArgumentParser()
    p.add_argument("--empresa", required=True)
    p.add_argument("--email", required=True)
    p.add_argument("--segmento", default=None)
    p.add_argument("--contato", default=None)
    p.add_argument("--cargo", default=None)
    p.add_argument("--necessidade", default=None)
    p.add_argument("--servico", default=None)
    args = p.parse_args()

    print("Gerando e-mail com o Copywriter...")
    req = CopywriterRequest(
        empresa=args.empresa,
        segmento=args.segmento,
        nome_contato=args.contato,
        cargo=args.cargo,
        canal="email",
        tipo="prospeccao",
        necessidade=args.necessidade,
        servico=args.servico,
        diferenciais=None,
        contexto_extra=None,
        lead_arquivo=None,
    )

    try:
        resp = gerar_email(req)
    except CopywriterError as e:
        print(f"Copywriter falhou: {e}")
        return

    email = resp.email
    print(f"   Gerado. Assunto: {email.assunto!r} (tom: {email.tom})")

    print("Salvando rascunho na caixa...")
    try:
        msg_id = salvar_rascunho(
            para=args.email,
            assunto=email.assunto,
            corpo=email.corpo,
        )
    except MailerError as e:
        print(f"❌ Mailer falhou: {e}")
        return

    print(f"   Rascunho criado (Message-ID: {msg_id})")
    print("   Abra o webmail e confira o rascunho!")


if __name__ == "__main__":
    main()