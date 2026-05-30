"""
Gera UM rascunho de teste apontando pro SEU e-mail e registra na tabela,
pra validar o ciclo completo: rascunho → enviar → confirmar → responder → detectar.

Uso:
    python scripts/teste_outreach.py --email "seu-email@gmail.com"
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import argparse
import asyncio
from datetime import datetime

from app.db.sync_bridge import bridge_session
from app.db.models.email_outreach import EmailOutreach
from app.mailer.client import salvar_rascunho


async def _criar(email_destino: str):
    assunto = "Teste de acompanhamento Reative"
    corpo = (
        "Olá! Este é um e-mail de teste do sistema de outreach.\n\n"
        "Se você respondê-lo, o sistema deve detectar a resposta.\n\n"
        "Pode ignorar — é só um teste interno."
    )

    print("Salvando rascunho de teste na caixa...")
    msg_id = salvar_rascunho(para=email_destino, assunto=assunto, corpo=corpo)

    async with bridge_session() as session:
        session.add(EmailOutreach(
            destinatario=email_destino,
            assunto=assunto,
            corpo=corpo,
            tom="teste",
            canal="email",
            follow_up_num=0,
            status="rascunho",
            message_id=msg_id,
            draft_criado_em=datetime.now(),
            contexto={"origem": "teste_outreach"},
        ))
        await session.commit()

    print(f"   Rascunho + registro criados (msg_id: {msg_id})")
    print("\n   PRÓXIMOS PASSOS:")
    print(f"   1. Abra o webmail, ache o rascunho 'Teste de acompanhamento Reative'")
    print(f"   2. Envie SEM EDITAR o destinatário (já está pro seu e-mail)")
    print(f"   3. Rode: python scripts/sync_emails.py")
    print(f"      → esperado: Enviados confirmados: 1")
    print(f"   4. Responda o e-mail do seu Gmail")
    print(f"   5. Rode o sync de novo → esperado: Respostas detectadas: 1")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True, help="Seu e-mail pra receber o teste")
    args = p.parse_args()
    asyncio.run(_criar(args.email))


if __name__ == "__main__":
    main()