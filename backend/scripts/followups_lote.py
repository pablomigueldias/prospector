import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import argparse
import asyncio

from app.mailer.outreach import gerar_followups_pendentes


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dias", type=int, default=3,
                   help="Só e-mails enviados há mais de X dias (default: 3)")
    p.add_argument("--max-followups", type=int, default=2,
                   help="Teto de toques por thread (default: 2)")
    p.add_argument("--limit", type=int, default=None,
                   help="Máx de follow-ups a gerar (default: todos)")
    p.add_argument("--pausa", type=float, default=8.0,
                   help="Segundos entre cada follow-up (default: 8)")
    args = p.parse_args()

    resumo = asyncio.run(
        gerar_followups_pendentes(
            dias=args.dias,
            max_followups=args.max_followups,
            limit=args.limit,
            pausa=args.pausa,
        )
    )
    print(f"  Follow-ups gerados: {resumo['gerados']}")
    print(f"  Falhas:             {resumo['falhas']}")


if __name__ == "__main__":
    main()