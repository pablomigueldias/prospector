# Perfil Mestre Freelancer — Pablo Miguel Dias

> Fonte da verdade sobre quem eu sou tecnicamente e o que eu já entreguei.
> **Tudo aqui é lastreado em repositório git real** (commits, stack, deploy) —
> nada inventado. É o insumo do redator/seletor do agente Workana, da descrição
> do perfil Workana, do LinkedIn e do GitHub.
>
> Regra de ouro: **reorganizo a verdade, nunca invento experiência.** Se não
> está num dos repos abaixo, não vai numa proposta.

---

## Headline (a frase que me posiciona)

**Desenvolvedor Full-Stack · Python/FastAPI · React/Next.js · Automação e IA**

Construo produtos de ponta a ponta: API assíncrona, banco versionado, frontend
moderno e *deploy de verdade em produção* — incluindo integração com LLMs,
autenticação robusta e bots. Não paro no "roda na minha máquina": coloco no ar.

---

## Qualidades técnicas (hard skills) — e onde cada uma aparece

Cada habilidade abaixo tem **prova num projeto**. A coluna "evidência" é o que eu
posso mostrar se o cliente pedir.

### Backend
- **Python moderno (3.11–3.12), type hints, código tipado** — todos os backends.
- **FastAPI** (assíncrono, Pydantic v2 pra validação) — Prospector, Content
  Factory, Portfolio, Churn (serving), Estudos.
- **SQLAlchemy 2.0 async + Alembic** (schema versionado em migrations no git) —
  Prospector, Content Factory, Portfolio.
- **PostgreSQL** (inclusive serverless/Neon e Postgres 16 em Docker) — todos.
- **Arquitetura em camadas / vertical slice** (router → service → schema →
  repository → model) — Prospector, com Clean Architecture/SOLID declarados no
  Portfolio.
- **Drivers async** (asyncpg) e sync (psycopg) convivendo, sabendo por quê.

### Frontend
- **React 18/19 e Next.js 14/16** (App Router e Pages Router) — Prospector,
  Reative Systems, Content Factory, Portfolio, landing-page.
- **TypeScript** ponta a ponta no front — Prospector, Reative Systems.
- **Tailwind CSS** + design system próprio (tokens OKLCH, tipografia, componentes
  reutilizáveis) — Prospector, Reative Systems.
- **Vite** pra build rápido — Portfolio, landing-page.
- **Framer Motion** (animação fluida), **Leaflet/react-leaflet** (mapas),
  **Swiper** (carrosséis), **Recharts** (gráficos de dados) — landing-page,
  Portfolio, Prospector.
- **SSG / rotas dinâmicas** (geração estática de páginas) — Reative Systems.

### Dados & Machine Learning
- **Pipeline de ML completo**: pandas, numpy, scikit-learn, tratamento de
  desbalanceamento (imbalanced-learn/SMOTE), avaliação com foco no **custo de
  negócio do erro** (FN vs FP), serialização do modelo (joblib) e *serving* via
  FastAPI — projeto Churn Prediction.
- **Jupyter / notebooks** pra exploração e visualização (matplotlib, seaborn).
- **Embeddings / busca semântica** (sentence-transformers) — Content Factory.

### IA / LLM aplicada
- **Integração com LLMs** com **provider trocável e fallback** (Gemini → Groq →
  Ollama) — Prospector. Também google-genai e Ollama local — Content Factory.
- **Padrão orquestrador** (orchestrator) pra encadear etapas de IA — Content
  Factory.
- **TTS / geração de voz** (chatterbox-tts) — Content Factory.
- **Engenharia de prompt estruturada** (prompt_builder + parser, saída em JSON
  validado) — Prospector.

### Infra, DevOps & Deploy
- **Deploy real em produção**: VPS Hetzner, domínio próprio
  (`studio.reativesystems.com.br`), acesso por chave SSH, usuário sem root —
  Prospector.
- **Docker / docker-compose** (Postgres 16, serviços) — Prospector, Content
  Factory.
- **Storage S3-compatível** (MinIO no VPS, portável pra S3 real, via boto3) —
  Prospector.
- **Agendador in-process** (APScheduler) pra cron/lembretes — Prospector.
- **Gestão de dependências** com Poetry (lock reprodutível) e requirements
  pinados — Content Factory, Portfolio, Prospector.

### Segurança & Autenticação
- **Hashing de senha forte** (Argon2id; também bcrypt) — Prospector, Portfolio.
- **2FA TOTP** (pyotp) com QR de setup e **secret cifrado em repouso** (Fernet) —
  Prospector.
- **RBAC** (papéis e permissões, ex.: `usuarios.gerenciar`) — Prospector.
- **JWT / criptografia** (python-jose, ecdsa), **rate limiting** — Portfolio.

### Integrações & Automação
- **Bot de Telegram** funcional em produção (lança gasto por mensagem, importa
  boleto por foto) — Prospector (@IqueFinBot).
- **Notion API** (sincroniza dados direto pro Notion) — Prospector.
- **Web scraping / automação de navegador** (Playwright, BeautifulSoup, lxml,
  httpx com SOCKS) — Prospector.
- **Cloudinary** (gestão dinâmica de assets) — Portfolio.

### Qualidade & Disciplina de engenharia
- **Testes automatizados** (pytest, inclusive marcados como integração) +
  **linter** (ruff) — Content Factory.
- **Testes E2E** (Playwright) + typecheck no CI do front — Prospector.
- **Migrations versionadas no git** (nada de alterar banco na mão).
- **Commits pequenos e frequentes** (Prospector: 261 commits; Portfolio: 114) —
  histórico legível, um passo por commit.
- **Documentação séria**: READMEs explicando decisões de arquitetura, docs de
  continuação e de deploy.


---

## Qualidades de processo (como eu trabalho)

Não são "buzzwords" — saem do jeito que os repos foram construídos:

- **Entrego em produção, não em protótipo.** O Prospector está no ar, com login,
  2FA, banco e bot reais. Sei o caminho inteiro: do código ao DNS.
- **Penso no negócio, não só no código.** No Churn, modelei o *custo* de cada
  tipo de erro porque um falso negativo (perder cliente sem avisar) custa mais
  que um falso positivo. Decisão de produto, não só de algoritmo.
- **Disciplina de versionamento.** Commits atômicos, mensagens descritivas,
  schema do banco versionado. Dá pra outra pessoa entrar no projeto e entender.
- **Reuso e consistência.** Crio design system e padrões (vertical slice) e os
  repito — não reinvento a roda a cada feature.
- **Migração e evolução, não só "do zero".** Reative Systems foi *migrado* de
  React-no-navegador pra Next.js profissional — sei pegar legado e modernizar.
- **Aprendo de forma estruturada.** Mantenho um repo de Estudos (FastAPI, type
  hints) — me atualizo de propósito.

---

## Portfólio — projeto a projeto (problema → solução → stack → evidência)

> Ordem pensada pra proposta: os 3 primeiros são os que eu destaco na Workana.

### 1. Prospector / Reative Studio — Plataforma de agentes (carro-chefe)
- **Problema:** centralizar vários "agentes" de trabalho (prospecção de leads,
  copywriting, outreach, organizador financeiro) numa plataforma só, com login e
  multiusuário.
- **Solução:** plataforma full-stack multiagente, em produção, com área de
  trabalho (Reative) e área pessoal separadas; autenticação completa; bot de
  Telegram; integrações externas.
- **Stack:** FastAPI async, SQLAlchemy 2.0, Alembic, PostgreSQL, Next.js 14 + TS
  + Tailwind + Recharts; LLM com fallback (Gemini/Groq/Ollama); Auth Argon2id +
  TOTP 2FA + RBAC + Fernet; Playwright; Notion API; MinIO/boto3; APScheduler;
  Docker; deploy em VPS Hetzner com domínio e SSH.
- **Evidência:** **261 commits**, ~5 semanas de trabalho contínuo, **no ar** em
  `studio.reativesystems.com.br`, bot `@IqueFinBot` ativo.

### 2. Content Factory — Geração de conteúdo com IA
- **Problema:** produzir conteúdo (texto + voz) de forma automatizada e
  orquestrada.
- **Solução:** backend com pipeline orquestrado de IA, busca semântica por
  embeddings e geração de voz (TTS), com frontend Next.js.
- **Stack:** FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16 (Docker), Next 16 +
  React 19; google-genai + Ollama; sentence-transformers (embeddings);
  chatterbox-tts; Poetry; pytest + ruff.
- **Evidência:** **54 commits**, suíte de testes (incl. testes de integração),
  arquitetura em `orchestrator/providers/models/schemas/api`.

### 3. Portfolio Profissional + Blog técnico
- **Problema:** ter um portfólio/blog próprio que *demonstre* a arquitetura, não
  só liste projetos.
- **Solução:** sistema desacoplado (backend RESTful + frontend SPA) com blog que
  renderiza matemática (KaTeX), gestão de mídia e autenticação.
- **Stack:** FastAPI + Poetry, PostgreSQL serverless (Neon), SQLAlchemy +
  Alembic, bcrypt + JWT + rate limiting, Cloudinary, google-generativeai; React
  19 + Vite + Tailwind + Framer Motion; KaTeX/markdown. Clean Architecture,
  SOLID e CI/CD declarados.
- **Evidência:** **114 commits**.

### 4. Churn Prediction — Machine Learning aplicado a negócio
- **Problema:** prever quais clientes vão cancelar (evasão) *antes* da perda,
  pra agir a tempo.
- **Solução:** pipeline de ML completo, do dado ao modelo servido por API, com a
  função de custo desenhada em cima do impacto real (FN custa mais que FP).
- **Stack:** pandas, numpy, scikit-learn, imbalanced-learn (SMOTE),
  matplotlib/seaborn, Jupyter, joblib; serving via FastAPI.
- **Evidência:** **9 commits**, README com modelagem do problema de negócio e
  análise de custo dos erros.

### 5. Reative Systems — Site institucional
- **Problema:** site institucional profissional, rápido e fácil de manter.
- **Solução:** migração de HTML/React-no-navegador para Next.js 14 (App Router)
  com camada de conteúdo separada da apresentação, rotas dinâmicas e SSG.
- **Stack:** Next.js 14, TypeScript, design system em CSS variables; geração
  estática de páginas de serviço e blog.
- **Evidência:** **13 commits**, README documentando a arquitetura e a migração.

### 6. Landing Page Oil — Landing animada com mapa
- **Problema:** página de captura com forte apelo visual e localização.
- **Solução:** landing single-page com animações, carrossel e mapa interativo.
- **Stack:** React 19 + Vite + Tailwind v4 + Framer Motion + Leaflet + Swiper.
- **Evidência:** **14 commits**.

### 7. Estudos — Repositório de aprendizado
- **O quê:** exercícios de fundamentos (FastAPI "simple-api", type hints em
  Python). Mostra hábito de estudo deliberado.
- **Evidência:** **8 commits**.

---

## Stack consolidada (pros campos de "habilidades" da Workana/perfis)

**Linguagens:** Python, TypeScript, JavaScript, SQL.
**Backend:** FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic, PostgreSQL,
REST.
**Frontend:** React (18/19), Next.js (14/16), TypeScript, Tailwind CSS, Vite,
Framer Motion, Recharts, Leaflet.
**IA/Dados:** LLMs (Gemini/Groq/Ollama), embeddings (sentence-transformers), TTS,
scikit-learn, pandas, numpy, Jupyter.
**Infra/DevOps:** Docker, docker-compose, VPS (Linux/SSH), Poetry, MinIO/S3,
APScheduler.
**Segurança:** Argon2id/bcrypt, TOTP 2FA, JWT, RBAC, Fernet, rate limiting.
**Integrações/Automação:** Telegram bot, Notion API, Playwright, BeautifulSoup,
Cloudinary.
**Qualidade:** pytest, ruff, Playwright E2E, migrations versionadas, Git.

> Os **5 destaques** que eu marcaria numa proposta dependem do projeto, mas o par
> default é: **FastAPI + PostgreSQL**, **React/Next.js + TypeScript**, **IA/LLM**,
> **Deploy/Docker** e **Autenticação/Segurança**.
