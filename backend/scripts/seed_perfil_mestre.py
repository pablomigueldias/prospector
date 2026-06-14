"""Semeia o Perfil Mestre (pessoal_perfil_mestre) a partir dos projetos reais
do git do Pablo.

Filosofia: este script é a *fonte versionada* do que o git prova sobre você.
- Campos DERIVADOS do git (titulo, resumo, habilidades, projetos) são sempre
  reescritos — edite as listas abaixo e rode de novo.
- Campos HUMANOS que o git não conhece (tom_escrita, experiencias, formacao e o
  miolo de o_que_procuro) são PRESERVADOS se já existirem — rodar de novo não
  apaga o que você digitou na tela. Use --force pra sobrescrever tudo.

Uso:
    source backend/venv/bin/activate
    python backend/scripts/seed_perfil_mestre.py          # merge não-destrutivo
    python backend/scripts/seed_perfil_mestre.py --force  # sobrescreve humanos
    python backend/scripts/seed_perfil_mestre.py --dry    # só mostra, não grava
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import argparse
import asyncio
import json

from app.api.schemas.pessoal import PerfilMestreUpsert
from app.api.services.pessoal.perfil_service import get_perfil, salvar_perfil


# ════════════════════════════════════════════════════════════════════
# DADOS DERIVADOS DO GIT — edite à vontade; o script reescreve no banco.
# ════════════════════════════════════════════════════════════════════

NOME = "Pablo Miguel Dias"

TITULO = "Desenvolvedor Full-Stack · Python/FastAPI · React/Next.js · Automação e IA"

RESUMO = (
    "Desenvolvedor full-stack que entrega de ponta a ponta — API assíncrona "
    "(FastAPI), banco versionado (PostgreSQL + Alembic) e front moderno "
    "(React/Next.js/TypeScript). Tenho experiência real de colocar em produção "
    "(VPS Linux, Docker, autenticação robusta) e de integrar IA/LLMs em "
    "produtos, não só de prototipar."
)

# {nome, nivel, onde_usou}
HABILIDADES = [
    {"nome": "Python", "nivel": "avançado",
     "onde_usou": "backends do Prospector, Content Factory, Portfolio e Churn"},
    {"nome": "FastAPI", "nivel": "avançado",
     "onde_usou": "APIs assíncronas do Prospector, Content Factory, Portfolio e Churn"},
    {"nome": "SQLAlchemy 2.0 (async)", "nivel": "avançado",
     "onde_usou": "Prospector, Content Factory e Portfolio"},
    {"nome": "Alembic (migrations versionadas)", "nivel": "avançado",
     "onde_usou": "schema no git do Prospector e Content Factory"},
    {"nome": "PostgreSQL", "nivel": "avançado",
     "onde_usou": "todos os backends (incl. Neon serverless no Portfolio)"},
    {"nome": "Pydantic (validação)", "nivel": "avançado",
     "onde_usou": "todos os serviços FastAPI"},
    {"nome": "TypeScript", "nivel": "avançado",
     "onde_usou": "front do Prospector e do site Reative Systems"},
    {"nome": "React (18/19)", "nivel": "avançado",
     "onde_usou": "Prospector, Portfolio, Content Factory e landing-page"},
    {"nome": "Next.js (14/16)", "nivel": "avançado",
     "onde_usou": "Prospector, Reative Systems e Content Factory"},
    {"nome": "Tailwind CSS + design system próprio", "nivel": "avançado",
     "onde_usou": "Prospector e Reative Systems (tokens OKLCH)"},
    {"nome": "Vite", "nivel": "intermediário",
     "onde_usou": "Portfolio e landing-page"},
    {"nome": "Integração com LLMs (Gemini/Groq/Ollama)", "nivel": "avançado",
     "onde_usou": "provider com fallback no Prospector; google-genai/Ollama na Content Factory"},
    {"nome": "Engenharia de prompt (prompt_builder + parser JSON)", "nivel": "avançado",
     "onde_usou": "analyzers do Prospector"},
    {"nome": "Machine Learning (scikit-learn)", "nivel": "intermediário",
     "onde_usou": "pipeline de churn com SMOTE e função de custo de negócio"},
    {"nome": "Embeddings / busca semântica", "nivel": "intermediário",
     "onde_usou": "sentence-transformers na Content Factory"},
    {"nome": "Docker / docker-compose", "nivel": "intermediário",
     "onde_usou": "Prospector e Content Factory"},
    {"nome": "Deploy em VPS (Linux/SSH)", "nivel": "intermediário",
     "onde_usou": "Prospector no ar em studio.reativesystems.com.br"},
    {"nome": "Autenticação & segurança (Argon2id, TOTP 2FA, RBAC, JWT)", "nivel": "avançado",
     "onde_usou": "Prospector e Portfolio"},
    {"nome": "Bot de Telegram", "nivel": "intermediário",
     "onde_usou": "@IqueFinBot no organizador financeiro do Prospector"},
    {"nome": "Web scraping / automação (Playwright, BeautifulSoup)", "nivel": "intermediário",
     "onde_usou": "coleta e automação no Prospector"},
    {"nome": "Testes (pytest, Playwright E2E) + linter (ruff)", "nivel": "intermediário",
     "onde_usou": "Content Factory e Prospector"},
    {"nome": "Git (commits atômicos, fluxo disciplinado)", "nivel": "avançado",
     "onde_usou": "261 commits no Prospector, 114 no Portfolio"},
]

# {nome, descricao, prova, stack:[], link}
PROJETOS = [
    {
        "nome": "Prospector / Reative Studio",
        "descricao": (
            "Plataforma full-stack multiagente (prospecção, copywriting, "
            "outreach, organizador financeiro) com área de trabalho e área "
            "pessoal separadas, login multiusuário e bot de Telegram."
        ),
        "prova": (
            "Em produção em studio.reativesystems.com.br, com auth completa "
            "(Argon2id + TOTP 2FA + RBAC) e 261 commits."
        ),
        "stack": [
            "FastAPI", "SQLAlchemy 2.0 async", "Alembic", "PostgreSQL",
            "Next.js 14", "TypeScript", "Tailwind", "Recharts", "Docker",
            "MinIO/S3", "APScheduler", "Gemini/Groq/Ollama", "Playwright",
        ],
        "link": "https://studio.reativesystems.com.br",
    },
    {
        "nome": "Content Factory",
        "descricao": (
            "Backend orquestrado de geração de conteúdo com IA: texto via LLM, "
            "busca semântica por embeddings e síntese de voz (TTS)."
        ),
        "prova": (
            "54 commits, suíte de testes (incl. integração) + ruff; arquitetura "
            "orchestrator/providers/models/schemas."
        ),
        "stack": [
            "FastAPI", "SQLAlchemy 2.0", "Alembic", "PostgreSQL", "Next.js 16",
            "React 19", "Ollama", "google-genai", "sentence-transformers",
            "TTS", "Poetry", "pytest",
        ],
        "link": None,
    },
    {
        "nome": "Portfolio + Blog técnico",
        "descricao": (
            "Portfólio e blog desacoplado (API RESTful + SPA) com renderização "
            "de matemática (KaTeX), gestão de mídia e autenticação."
        ),
        "prova": (
            "114 commits; Clean Architecture/SOLID, Postgres serverless (Neon), "
            "JWT + rate limiting, Cloudinary."
        ),
        "stack": [
            "FastAPI", "Poetry", "PostgreSQL (Neon)", "SQLAlchemy", "Alembic",
            "JWT", "Cloudinary", "React 19", "Vite", "Tailwind", "Framer Motion",
            "KaTeX",
        ],
        "link": None,
    },
    {
        "nome": "Churn Prediction",
        "descricao": (
            "Pipeline de Machine Learning que prevê evasão de clientes, do dado "
            "ao modelo servido por API, com a função de custo desenhada no "
            "impacto de negócio (falso negativo custa mais que falso positivo)."
        ),
        "prova": (
            "9 commits; scikit-learn + SMOTE, README modelando o custo dos "
            "erros; serving em FastAPI."
        ),
        "stack": [
            "pandas", "numpy", "scikit-learn", "imbalanced-learn", "matplotlib",
            "seaborn", "Jupyter", "joblib", "FastAPI",
        ],
        "link": None,
    },
    {
        "nome": "Reative Systems — site institucional",
        "descricao": (
            "Site institucional migrado de HTML/React-no-navegador para Next.js "
            "14 (App Router), com conteúdo separado da apresentação, rotas "
            "dinâmicas e geração estática (SSG)."
        ),
        "prova": "13 commits; páginas de serviço e blog geradas estaticamente.",
        "stack": ["Next.js 14", "TypeScript", "App Router", "SSG", "CSS design system"],
        "link": None,
    },
    {
        "nome": "Landing Page Oil",
        "descricao": (
            "Landing single-page com forte apelo visual: animações, carrossel e "
            "mapa interativo."
        ),
        "prova": "14 commits.",
        "stack": ["React 19", "Vite", "Tailwind v4", "Framer Motion", "Leaflet", "Swiper"],
        "link": None,
    },
]

# {email, telefone, linkedin, github, portfolio} — o que o git não diz fica None.
CONTATO = {
    "email": "pablo.miguel.dias@gmail.com",
    "telefone": None,
    "linkedin": None,
    "github": "pablomigueldias",
    "portfolio": None,
}

# Só a stack desejada é derivável; o resto (modelo/pretensão) é seu, fica em branco.
OQUE_PROCURO_STACK = [
    "Python", "FastAPI", "PostgreSQL", "React", "Next.js", "TypeScript", "IA/LLM",
]


# ════════════════════════════════════════════════════════════════════
# Lógica de merge não-destrutivo
# ════════════════════════════════════════════════════════════════════

async def montar_payload(force: bool) -> PerfilMestreUpsert:
    atual = await get_perfil()
    base: dict = atual.model_dump() if atual else {}
    for k in ("id", "ativo", "created_at", "updated_at"):
        base.pop(k, None)

    # --- Derivados do git: sempre reescreve ---
    base["titulo"] = TITULO
    base["resumo"] = RESUMO
    base["habilidades"] = HABILIDADES
    base["projetos"] = PROJETOS

    # --- Humanos: só preenche se vazio (ou --force) ---
    if force or not base.get("nome"):
        base["nome"] = NOME
    if force or not base.get("contato"):
        base["contato"] = CONTATO

    oqp = base.get("o_que_procuro") or {}
    if force or not oqp.get("stack"):
        oqp["stack"] = OQUE_PROCURO_STACK
    base["o_que_procuro"] = oqp

    # tom_escrita, experiencias, formacao, blocos_curriculo: preservados como estão

    return PerfilMestreUpsert(**base)


async def main(force: bool, dry: bool) -> None:
    payload = await montar_payload(force)

    if dry:
        print(json.dumps(payload.model_dump(), indent=2, ensure_ascii=False))
        print("\n[dry-run] nada foi gravado.")
        return

    salvo = await salvar_perfil(payload)
    print("✓ Perfil Mestre gravado.")
    print(f"  nome:        {salvo.nome}")
    print(f"  titulo:      {salvo.titulo}")
    print(f"  habilidades: {len(salvo.habilidades)}")
    print(f"  projetos:    {len(salvo.projetos)}")
    print(f"  experiencias:{len(salvo.experiencias)}  (preservadas — preencha na tela)")
    print(f"  tom_escrita: {'definido' if salvo.tom_escrita else 'vazio — preencha na tela'}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Semeia o Perfil Mestre a partir do git.")
    p.add_argument("--force", action="store_true",
                   help="sobrescreve também os campos humanos (nome, contato, o_que_procuro.stack)")
    p.add_argument("--dry", action="store_true", help="mostra o payload e não grava")
    args = p.parse_args()
    asyncio.run(main(args.force, args.dry))
