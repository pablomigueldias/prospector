"""
Sincroniza o status dos e-mails: confirma enviados e detecta respostas.
Rode periodicamente (algumas vezes ao dia) depois de enviar e-mails.

Uso:
    python scripts/sync_emails.py            # últimos 30 dias
    python scripts/sync_emails.py --dias 7   # só a última semana
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import argparse
from app.mailer.sync import sincronizar


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dias", type=int, default=30)
    args = p.parse_args()

    print("Sincronizando e-mails...")
    r = sincronizar(dias=args.dias)
    print("=" * 50)
    print(f"  Enviados confirmados: {r['enviados_confirmados']}")
    print(f"  Respostas detectadas: {r['respostas_detectadas']}")
    print("=" * 50)


if __name__ == "__main__":
    main()