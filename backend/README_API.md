# Backend — Plataforma de Agentes da Reativa

API FastAPI que orquestra os agentes da plataforma. Hoje serve o **Prospector**; está pronta pra plugar novos agentes (Cobrança, Suporte, Onboarding) sem reescrever a base.

> Pra visão geral do projeto inteiro, veja [`../README.md`](../README.md).

---

## Quickstart

```bash
# Da raiz do monorepo
cd backend

# 1. Cria virtualenv (uma vez só)
python3 -m venv venv
source venv/bin/activate         # Linux/Mac
# venv\Scripts\activate          # Windows

# 2. Instala deps
pip install -r requirements.txt

# 3. Configura secrets
cp .env.example .env
# Edita .env com:
#   NOTION_TOKEN=secret_xxx
#   NOTION_DB_EMPRESAS=xxxxxx
#   NOTION_DB_CONTATOS=xxxxxx
#   GEMINI_API_KEY=xxxxxx

# 4. Sobe a API
python run.py serve
```

Pronto:
- API em **http://localhost:8000**
- Swagger interativo em **http://localhost:8000/docs**
- Healthcheck em **http://localhost:8000/api/health**

---

## Estrutura

```
backend/
├── run.py                          ← CLI + comando `serve` (uvicorn)
├── requirements.txt
├── .env.example                    ← Template dos secrets
│
├── app/
│   ├── api/                        ← Camada HTTP
│   │   ├── main.py                 ← FastAPI app + CORS + lifespan
│   │   ├── registry.py             ← Registro central dos agentes ⭐
│   │   ├── routers/
│   │   │   ├── agents.py           ← GET /api/agents
│   │   │   └── prospector.py       ← POST /preview, /manual, GET /leads
│   │   ├── schemas/
│   │   │   └── prospector.py       ← Pydantic (request/response)
│   │   └── services/
│   │       ├── prospector_service.py  ← Wrapper do pipeline
│   │       └── leads_reader.py     ← Lê data/sent/*.json
│   │
│   ├── collectors/                 ← Fontes de dados
│   │   ├── brasilapi/              ← BrasilAPI + fallback OpenCNPJ ⭐
│   │   │   ├── __init__.py         ← Orquestrador
│   │   │   ├── client.py           ← Cliente BrasilAPI
│   │   │   ├── opencnpj_client.py  ← Cliente OpenCNPJ
│   │   │   ├── normalizers.py      ← OpenCNPJ → formato BrasilAPI
│   │   │   ├── mappers.py          ← JSON → Lead (Pydantic)
│   │   │   └── classifiers.py      ← Setor por CNAE, tamanho por porte
│   │   ├── website/                ← Scraping de site
│   │   │   ├── crawler.py          ← httpx + escalação Playwright
│   │   │   ├── client.py           ← fetch_html (HTTP/Playwright)
│   │   │   ├── extractors.py       ← Regex pra email/tel/whats/IG/FB
│   │   │   └── cache.py
│   │   └── buscadores/             ← DDG/Brave/Bing (modo investigar)
│   │
│   ├── analyzers/
│   │   └── gemini.py               ← Análise IA, vai pras Notas
│   │
│   ├── exporters/
│   │   └── notion/                 ← Cria/atualiza páginas no Notion
│   │       ├── exporter.py
│   │       ├── mappers.py
│   │       ├── property_builder.py
│   │       └── repository.py
│   │
│   ├── models/
│   │   └── lead.py                 ← Lead, Empresa, Contato (Pydantic)
│   │
│   ├── services/
│   │   └── manual_overrides.py     ← Aplica --whats, --email, --ig etc
│   │
│   └── utils/
│       ├── logger.py               ← Loguru pré-configurado
│       └── storage.py              ← Salva/lê data/{raw,processed,sent}/
│
└── data/                           ← Backups locais (.gitignore)
    ├── raw/                        ← Snapshot após coleta
    ├── processed/                  ← Após análise IA
    ├── sent/                       ← Após envio pro Notion
    ├── cache/                      ← Cache HTTP do scraper
    └── sessao/                     ← Cookies dos buscadores
```

---

## Pipeline do Prospector (passo a passo)

Quando você roda `prospectar-full <CNPJ>`, esta sequência acontece:

```
1. Valida CNPJ localmente (dígitos verificadores)
   ↓
2. BrasilAPI consulta o CNPJ
   ├─ Sucesso? Vai pro passo 3
   ├─ 404? Tenta OpenCNPJ (mesma cara, fonte independente)
   └─ Erro 5xx? Tenta OpenCNPJ
   ↓
3. map_to_lead(json) → Lead (Empresa + 1 Contato por sócio)
   • Setor classificado pelo CNAE (primeiros 2 dígitos)
   • Tamanho pelo porte (ME, EPP, Demais)
   • Telefone fixo da OpenCNPJ → 1º contato (se houver)
   • Email da Receita → Notas (é do contador)
   ↓
4. Scraping do site (se URL informada)
   ├─ httpx primeiro (rápido)
   ├─ Escala pro Playwright se: HTML < 500 chars OU parece_spa()
   └─ Extrai email/whats/tel/IG/FB/LinkedIn → 1º contato e empresa
   ↓
5. Overrides manuais (--whats, --email, --ig etc)
   • Input manual SEMPRE prevalece (você sabe o que digitou)
   ↓
6. Análise IA com Gemini → anexa nas Notas da empresa
   ↓
7. Salva backup em data/processed/
   ↓
8. Envia pro Notion (cria/atualiza Empresa + Contatos)
   ↓
9. Salva backup em data/sent/
```

---

## CLI — Comandos disponíveis

Tudo via `python run.py <comando> [args]`. Roda dentro do venv ativado.

### Pipeline completo

```bash
# Modo manual (recomendado quando você tem CNPJ + site)
python run.py prospectar-full <CNPJ> [URL]

# Com overrides manuais (sobrescrevem o que veio do scraping)
python run.py prospectar-full --cnpj 52346129000150 --site https://x.com.br \
  --ig @empresa \
  --fb empresa \
  --linkedin joao-silva \
  --email contato@empresa.com.br \
  --tel "(11) 3234-5678" \
  --whats "(11) 91234-5678"
```

### Diagnóstico

```bash
# API: tudo funcionando?
python run.py serve

# Site não cede contatos? Investigue:
python run.py debug-site https://endolive.com.br/
python run.py debug-site https://endolive.com.br/ --playwright

# Notion conectado?
python run.py test-notion
```

### Outros (modo "investigar" com buscadores)

```bash
python run.py investigar --nome "Padaria do Zé" --cidade "São Paulo"
python run.py tor-status
python run.py test-buscadores "padaria são paulo"
```

---

## API HTTP — Endpoints

Documentação interativa: **http://localhost:8000/docs**

| Método | Rota | O que faz |
|--------|------|-----------|
| `GET` | `/api/health` | Healthcheck |
| `GET` | `/api/agents` | Lista os agentes da plataforma (alimenta a sidebar do front) |
| `GET` | `/api/agents/{slug}` | Detalhe de um agente |
| `POST` | `/api/agents/prospector/preview` | Monta o Lead **sem mandar pro Notion** (~2-5s) |
| `POST` | `/api/agents/prospector/manual` | Pipeline completo **com envio pro Notion** (30s-2min) |
| `GET` | `/api/agents/prospector/leads?limit=20` | Histórico de leads enviados (do backup local) |

### Exemplo — preview

```bash
curl -X POST http://localhost:8000/api/agents/prospector/preview \
  -H "Content-Type: application/json" \
  -d '{
    "cnpj": "52346129000150",
    "site": "https://climadiagnosticos.com.br/"
  }' | python3 -m json.tool
```

### Exemplo — pipeline completo

```bash
curl -X POST http://localhost:8000/api/agents/prospector/manual \
  -H "Content-Type: application/json" \
  -d '{
    "cnpj": "52346129000150",
    "site": "https://climadiagnosticos.com.br/",
    "whatsapp": "(11) 99208-0886"
  }' | python3 -m json.tool
```

---

## Schema do Notion

A integração espera **dois bancos de dados** no Notion:

### `NOTION_DB_EMPRESAS`

| Propriedade | Tipo | Origem |
|-------------|------|--------|
| Nome | Title | nome fantasia (fallback razão social) |
| Razão social | Rich text | BrasilAPI/OpenCNPJ |
| CNPJ | Rich text | BrasilAPI/OpenCNPJ |
| Cidade, Estado | Rich text | BrasilAPI/OpenCNPJ |
| Setor | Select | Classificado pelo CNAE |
| Tamanho | Select | "ME (1-10)", "Média (11-50)", "Grande (50+)" |
| Capital social | Number | BrasilAPI/OpenCNPJ |
| Site | URL | input ou descoberto |
| Instagram, Facebook | URL | scraping + overrides |
| Notas | Rich text | extras + análise IA |

### `NOTION_DB_CONTATOS`

| Propriedade | Tipo | Origem |
|-------------|------|--------|
| Nome | Title | sócio (QSA) ou contato comercial |
| Cargo | Rich text | qualificação do QSA |
| Email, Telefone, WhatsApp | Email/Phone | site + overrides + OpenCNPJ |
| LinkedIn | URL | scraping + overrides (LinkedIn da PESSOA) |
| Decisor | Checkbox | true pra sócios |
| Empresa | Relation → DB Empresas | linka automaticamente |

---

## Como adicionar um novo agente

A arquitetura é **data-driven**. Pra plugar "Cobrança", por exemplo:

### 1. Registre o agente em `app/api/registry.py`

```python
_AGENTS: List[Agent] = [
    Agent(slug="prospector", ...),
    Agent(                             # ← adicione aqui
        slug="cobranca",
        name="Cobrança",
        description="Acompanha boletos e dispara lembretes",
        icon="ti-cash",
        status="active",
        order=20,
        capabilities={"manual": True, "auto_send": False},
    ),
]
```

### 2. Crie o router em `app/api/routers/cobranca.py`

Espelhe a estrutura de `prospector.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/agents/cobranca", tags=["cobranca"])

@router.post("/disparar")
def cobranca_disparar(body: CobrancaRequest) -> CobrancaResponse:
    # sua lógica aqui
    ...
```

### 3. Plugue no `app/api/main.py`

```python
from app.api.routers import cobranca as cobranca_router
app.include_router(cobranca_router.router)
```

### 4. (Opcional) Crie o service de negócio em `app/api/services/cobranca_service.py`

Pra manter a regra **rotas finas, services grossos** — facilita testar isolado.

Pronto. A sidebar do frontend descobre sozinha. Sem mudar nada lá.

---

## Como testar

```bash
# Testes locais isolados (sem rede)
python3 -m pytest tests/      # se você tiver suíte criada

# Smoke test via TestClient FastAPI
python3 -c "
from fastapi.testclient import TestClient
from app.api.main import app
c = TestClient(app)
r = c.get('/api/agents')
print(r.json())
"
```
