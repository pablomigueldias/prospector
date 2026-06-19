"""Carrega as certificações do Pablo no Perfil Mestre ativo (Fase 0 do plano MAS).

Fonte: Drive público de certificados. Catálogo abaixo é a fonte versionada —
edite a lista e rode de novo. Merge NÃO-destrutivo por padrão: preserva o resto
do perfil e não duplica certificação já presente (casa por `nome`).

Uso:
    python backend/scripts/seed_certificacoes.py          # merge (idempotente)
    python backend/scripts/seed_certificacoes.py --force  # substitui a lista toda
    python backend/scripts/seed_certificacoes.py --dry    # só mostra, não grava
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import argparse
import asyncio

from app.api.schemas.pessoal import Certificacao, PerfilMestreUpsert
from app.api.services.pessoal.perfil_service import get_perfil, salvar_perfil

# ════════════════════════════════════════════════════════════════════
# CATÁLOGO — 27 certificados (nome, tema, o que comprova).
# ════════════════════════════════════════════════════════════════════
CERTIFICACOES = [
    # Frontend / Web
    {"nome": "HTML5", "tema": "Frontend", "prova": "marcação semântica e estrutura de páginas web"},
    {"nome": "HTML5 (nano)", "tema": "Frontend", "prova": "fundamentos de HTML5"},
    {"nome": "CSS3", "tema": "Frontend", "prova": "estilização, layout e responsividade com CSS3"},
    {"nome": "Frontend com React e JavaScript", "tema": "Frontend", "prova": "construção de interfaces com React e JavaScript"},
    {"nome": "Do Figma ao Código", "tema": "Frontend", "prova": "handoff design→código a partir do Figma"},

    # Backend / Linguagens
    {"nome": "Python 3 — Mundo 1", "tema": "Backend", "prova": "fundamentos de Python 3"},
    {"nome": "Python 3 — Mundo 2", "tema": "Backend", "prova": "estruturas e lógica intermediária em Python 3"},
    {"nome": "Introdução à Lógica de Programação", "tema": "Backend", "prova": "raciocínio algorítmico e lógica"},
    {"nome": "Introdução à Orientação a Objetos", "tema": "Backend", "prova": "fundamentos de POO"},

    # Banco de Dados / Dados
    {"nome": "Criando Sistemas de Banco de Dados", "tema": "Dados", "prova": "modelagem e criação de bancos de dados"},
    {"nome": "SQL Server 2016 — Programação em T-SQL", "tema": "Dados", "prova": "programação T-SQL em SQL Server"},
    {"nome": "MongoDB — Introdução", "tema": "Dados", "prova": "fundamentos de banco NoSQL com MongoDB"},
    {"nome": "Big Data — Introdução e Oportunidades", "tema": "Dados", "prova": "conceitos de Big Data"},

    # IA / Machine Learning
    {"nome": "Fundamentos de Machine Learning", "tema": "IA/ML", "prova": "fundamentos de aprendizado de máquina"},
    {"nome": "Formação Completa em Inteligência Artificial", "tema": "IA/ML", "prova": "panorama aplicado de IA"},
    {"nome": "Fundamentos de IA e Chatbot com IBM Watson", "tema": "IA/ML", "prova": "construção de chatbots com IBM Watson"},
    {"nome": "Domine a IA com Gemini", "tema": "IA/ML", "prova": "uso aplicado do Google Gemini"},
    {"nome": "Prompting — Maximizar a IA no seu Negócio", "tema": "IA/ML", "prova": "engenharia de prompt aplicada a negócios"},
    {"nome": "Como Criar Agentes de IA Avançado", "tema": "IA/ML", "prova": "construção de agentes de IA (base deste roadmap MAS)"},

    # Infra / Redes / Segurança
    {"nome": "Conceitos e Infraestrutura de Redes", "tema": "Infra/Redes", "prova": "fundamentos de redes e infraestrutura"},
    {"nome": "SOC — Security Operations Center", "tema": "Segurança", "prova": "noções de operação de segurança (SOC)"},

    # Ferramentas / CRM (Zoho)
    {"nome": "Zoho CRM", "tema": "Zoho/CRM", "prova": "operação e configuração do Zoho CRM"},
    {"nome": "Console do Administrador do Zoho Mail", "tema": "Zoho/CRM", "prova": "administração do Zoho Mail"},
    {"nome": "Zoho Desk — Primeiros Passos", "tema": "Zoho/CRM", "prova": "fundamentos de atendimento no Zoho Desk"},
    {"nome": "Zoho Desk — Atendimento Omnichannel", "tema": "Zoho/CRM", "prova": "atendimento omnichannel com Zoho Desk"},

    # Soft skills / Gestão
    {"nome": "Coaching para Alta Performance em TI", "tema": "Gestão/Soft skills", "prova": "performance e desenvolvimento de times de TI"},
    {"nome": "Liderança Corporativa", "tema": "Gestão/Soft skills", "prova": "fundamentos de liderança corporativa"},
]


async def main(force: bool, dry: bool) -> None:
    perfil = await get_perfil()
    if perfil is None:
        print("✗ Não há Perfil Mestre ativo. Rode seed_perfil_mestre.py primeiro.")
        sys.exit(1)

    atuais = list(perfil.certificacoes or [])
    if force:
        novas = list(CERTIFICACOES)
    else:
        novas = [c.model_dump() for c in atuais]
        ja_tem = {c.nome.strip().lower() for c in atuais}
        for c in CERTIFICACOES:
            if c["nome"].strip().lower() not in ja_tem:
                novas.append(c)

    print(f"Certificações atuais: {len(atuais)} → resultado: {len(novas)}")
    if dry:
        for c in novas:
            print(f"  - {c['nome']} [{c.get('tema')}]")
        print("\n(dry-run — nada gravado)")
        return

    payload = PerfilMestreUpsert(
        **perfil.model_dump(exclude={"id", "ativo", "created_at", "updated_at", "certificacoes"}),
        certificacoes=[Certificacao(**c) for c in novas],
    )
    salvo = await salvar_perfil(payload)
    print(f"✓ Perfil salvo com {len(salvo.certificacoes)} certificações.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="substitui a lista toda")
    ap.add_argument("--dry", action="store_true", help="só mostra, não grava")
    args = ap.parse_args()
    asyncio.run(main(force=args.force, dry=args.dry))
