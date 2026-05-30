import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import argparse
import asyncio

from app.mailer.outreach import gerar_rascunhos_pendentes


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--pausa", type=float, default=8.0)
    args = p.parse_args()

    resumo = asyncio.run(
        gerar_rascunhos_pendentes(limit=args.limit, pausa=args.pausa)
    )
    print(f"  Gerados:  {resumo['gerados']}")
    print(f"  Falhas:   {resumo['falhas']}")
    print(f"  Pulados:  {resumo['pulados']}")


if __name__ == "__main__":
    main()