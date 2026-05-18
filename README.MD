#  Reative Systems — Plataforma de Agentes

Plataforma interna da Reative Systems pra orquestrar **agentes de IA** que automatizam processos comerciais e operacionais. O primeiro agente em produção é o **Prospector**; outros (Cobrança, Suporte, Onboarding) estão no roadmap.

> **Estado atual:** Prospector ativo. Backend Python + frontend Next.js rodando local.
> **Próximo:** Cobrança, Suporte, Onboarding.

---

## Visão geral

A plataforma é um **monorepo** com duas camadas que conversam por HTTP:

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14 + TypeScript + Tailwind)              │
│  • Dashboard de agentes — http://localhost:3000             │
│  • Design system Reativa (OKLCH, Space Grotesk, Manrope)    │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTP/JSON (REST)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI + Python 3.10+)                           │
│  • API HTTP — http://localhost:8000                         │
│  • Pipeline do Prospector: BrasilAPI → OpenCNPJ → site →    │
│    análise IA (Gemini) → Notion                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  Notion (CRM)        │
                │  • DB Empresas       │
                │  • DB Contatos       │
                └──────────────────────┘
```

### O que o Prospector faz

Você passa um **CNPJ** (e opcionalmente um site, redes sociais ou contatos manuais) e o pipeline:

1. **Busca dados cadastrais** — BrasilAPI primeiro; se 404 ou erro, OpenCNPJ como fallback
2. **Cria a Empresa + um Contato por sócio** (decisor) automaticamente
3. **Faz scraping do site** — extrai email, WhatsApp, telefone, Instagram, Facebook, LinkedIn (e escala pro Playwright se for SPA)
4. **Aplica overrides manuais** — se você passou `--whats`, `--email` etc, sobrescreve o que veio de fontes automáticas
5. **Análise IA com Gemini** — gera resumo, classificação setor/tamanho, sinais de qualificação
6. **Envia tudo pro Notion** — cria/atualiza páginas nos DBs de Empresas e Contatos

Tudo isso disponível por:
- **CLI** — `python run.py prospectar-full <CNPJ> [URL] [flags]`
- **API HTTP** — `POST /api/agents/prospector/manual`
- **Frontend** — formulário visual em http://localhost:3000

---

## Estrutura do monorepo

```
prospector/
├── README.md                  ← este arquivo (visão geral)
├── .gitignore
│
├── backend/                   ← Python / FastAPI (ver backend/README.md)
│   ├── app/
│   │   ├── api/               ← FastAPI (rotas, schemas, services)
│   │   ├── collectors/        ← BrasilAPI, OpenCNPJ, site scraper, buscadores
│   │   ├── analyzers/         ← Gemini (análise IA)
│   │   ├── exporters/         ← Notion exporter
│   │   ├── models/            ← Pydantic (Lead, Empresa, Contato)
│   │   ├── services/          ← Overrides manuais e outros serviços
│   │   └── utils/             ← Logger, storage, etc.
│   ├── data/                  ← Backups locais (ignorado pelo Git)
│   │   ├── raw/, processed/, sent/   ← snapshots do pipeline
│   │   ├── cache/             ← cache HTTP do scraper
│   │   └── sessao/            ← cookies dos buscadores
│   ├── logs/                  ← Logs do servidor (ignorado)
│   ├── run.py                 ← CLI + comando `serve` (sobe FastAPI)
│   ├── requirements.txt
│   └── .env                   ← Tokens (NÃO versionar)
│
└── frontend/                  ← Next.js / TypeScript (ver frontend/README.md)
    ├── pages/                 ← Rotas (_app, _document, index, agents/[slug])
    ├── components/            ← Sidebar, Topbar, ProspectorForm, etc.
    ├── hooks/                 ← useAgents, useProspector, useFetch
    ├── lib/                   ← api.ts (cliente HTTP), types.ts, format.ts
    ├── styles/                ← globals.css (Tailwind + componentes)
    ├── tailwind.config.ts     ← Design system Reativa (OKLCH)
    ├── package.json
    └── .env.local             ← URL da API (NÃO versionar)
```

---

## Quickstart (primeiro uso)

### Pré-requisitos
- **Python 3.10+**
- **Node.js 18.17+**
- **Conta Notion** com dois bancos: `Empresas` e `Contatos` (schema descrito em [backend/README.md](backend/README.md))
- **API key do Google Gemini**

### 1. Clone e configure os secrets

```bash
git clone <seu-repo>
cd prospector

# Backend
cd backend
cp .env.example .env
# Edita .env com seus tokens:
#   NOTION_TOKEN=secret_xxx
#   NOTION_DB_EMPRESAS=xxxxxx
#   NOTION_DB_CONTATOS=xxxxxx
#   GEMINI_API_KEY=xxxxxx

# Frontend
cd ../frontend
cp .env.local.example .env.local
# O default já aponta pra http://localhost:8000 — só mexa se a porta da API mudar
```

### 2. Instale as dependências

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate          # Linux/Mac
# ou: venv\Scripts\activate       # Windows
pip install -r requirements.txt

# Frontend (em outro terminal)
cd frontend
npm install
```

### 3. Rode os dois serviços (em terminais separados)

```bash
# Terminal 1 — backend
cd backend
source venv/bin/activate
python run.py serve
# → API rodando em http://localhost:8000
# → Swagger interativo em http://localhost:8000/docs

# Terminal 2 — frontend
cd frontend
npm run dev
# → Dashboard em http://localhost:3000
```

### 4. Use!

Abra **http://localhost:3000** no navegador. Ele redireciona pra tela do Prospector — preencha o CNPJ e clique em "Pré-visualizar lead" ou "Prospectar e enviar pro Notion".

---

## Testes rápidos

### Saúde da API
```bash
curl http://localhost:8000/api/health
# {"status":"ok","service":"reativa-agents-api"}
```

### Pipeline pelo CLI (sem o frontend)
```bash
cd backend
source venv/bin/activate
python run.py prospectar-full 52346129000150 https://climadiagnosticos.com.br/
```

### Diagnosticar site que não cede contatos
```bash
python run.py debug-site https://endolive.com.br/
python run.py debug-site https://endolive.com.br/ --playwright   # força JS
```

### Diagnosticar conexão frontend → backend
Abre **http://localhost:3000/diagnostico** no navegador (se você ainda não removeu o arquivo `pages/diagnostico.tsx`). Mostra cada endpoint ✅ ou ❌.

---

## Como adicionar um novo agente

A arquitetura é **data-driven** — você não reescreve nada do dashboard pra plugar um novo agente:

**1. Backend** — anexa em `backend/app/api/registry.py`:
```python
Agent(
    slug="cobranca",
    name="Cobrança",
    description="Acompanha boletos e dispara lembretes no WhatsApp",
    icon="ti-cash",
    status="active",        # ← muda de "soon" pra "active" quando estiver pronto
    order=20,
),
```

**2. Backend** — crie a lógica em `backend/app/api/routers/cobranca.py` espelhando `prospector.py`.

**3. Backend** — plugue no `backend/app/api/main.py`:
```python
from app.api.routers import cobranca as cobranca_router
app.include_router(cobranca_router.router)
```

**4. Frontend** — em `frontend/pages/agents/[slug].tsx`, adicione o branch:
```tsx
{agent.slug === 'prospector' ? <ProspectorScreen ... />
 : agent.slug === 'cobranca' ? <CobrancaScreen ... />
 : <ComingSoonScreen ... />}
```

Pronto. A sidebar descobre sozinha via `GET /api/agents`.

Detalhes específicos de cada parte:
- **Backend** → [`backend/README.md`](backend/README.md)
- **Frontend** → [`frontend/README.md`](frontend/README.md)

---

## Segurança e privacidade

- **Nenhum token vai pro Git.** O `.gitignore` bloqueia `.env`, `.env.local`, chaves, certificados.
- **Dados de prospects não vão pro Git.** Os backups locais em `backend/data/{raw,processed,sent,cache,sessao}/` são ignorados — eles contêm CNPJs, sócios, telefones e emails reais.
- **CORS restrito a `localhost:3000`** em dev. Pra produção, edite `backend/app/api/main.py` e adicione o domínio real.
- **Não há autenticação no backend hoje.** É local apenas. Pra publicar pra equipe, adicione middleware de auth (token Bearer ou OAuth) antes de subir.

---

## Stack

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Backend | Python + FastAPI + Pydantic | 3.10+ / 0.115+ |
| Frontend | Next.js + React + TypeScript | 14 / 18 / 5 |
| Estilos | Tailwind CSS + design system Reativa | 3.4 |
| CRM | Notion (notion-client) | — |
| IA | Google Gemini | — |
| HTTP cliente | httpx + tenacity (retry) | — |
| Scraping JS | Playwright Chromium (opcional) | — |

---

## Roadmap

| Agente | Status |
|--------|--------|
| **Prospector** | ✅ Ativo |
| Cobrança | 🗓️ Q3 |
| Suporte | 🗓️ Q3 |
| Onboarding | 🗓️ Q4 |

### Backlog técnico

- [ ] Página de detalhe do lead (`/agents/prospector/leads/[arquivo]`)
- [ ] Filtros no histórico (setor, fonte, data)
- [ ] Tela de Métricas (gráficos de leads/dia, taxa de uso por fonte)
- [ ] Autenticação real (NextAuth + JWT no backend)
- [ ] Deploy: Vercel (front) + Railway/Render (back)
- [ ] Dark mode
- [ ] Importação CSV em lote
- [ ] Modo `--playwright` automático quando o site não cede dados

---

## 📜 Licença

Propriedade da Reative Systems. Uso interno.