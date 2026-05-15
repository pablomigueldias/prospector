# API HTTP — Plataforma de Agentes da Reativa

FastAPI servindo o backend pro frontend Next.js. Hoje expõe o agente
Prospector; a estrutura está pronta pra plugar novos agentes.

## Como rodar

1. Instale as deps novas (uma vez só):
   ```bash
   pip install fastapi 'uvicorn[standard]'
   ```

2. Suba a API:
   ```bash
   python run.py serve
   ```
   Ou direto via uvicorn (mais controle):
   ```bash
   uvicorn app.api.main:app --reload --port 8000
   ```

3. Pronto. Acesse:
   - **Swagger interativo:** http://localhost:8000/docs
   - **Healthcheck:** http://localhost:8000/api/health

## Endpoints disponíveis

| Método | Rota | O que faz |
|--------|------|-----------|
| `GET`  | `/api/health` | Healthcheck |
| `GET`  | `/api/agents` | Lista todos os agentes da plataforma |
| `GET`  | `/api/agents/{slug}` | Detalhe de um agente específico |
| `POST` | `/api/agents/prospector/preview` | Monta o Lead sem mandar pro Notion |
| `POST` | `/api/agents/prospector/manual` | Pipeline completo + envio pro Notion |
| `GET`  | `/api/agents/prospector/leads?limit=20` | Histórico recente (backup local) |

## Como testar via curl

```bash
# Healthcheck
curl http://localhost:8000/api/health

# Listar agentes
curl http://localhost:8000/api/agents | python -m json.tool

# Pré-visualizar lead (não envia pro Notion)
curl -X POST http://localhost:8000/api/agents/prospector/preview \
  -H "Content-Type: application/json" \
  -d '{
    "cnpj": "52346129000150",
    "site": "https://climadiagnosticos.com.br/"
  }' | python -m json.tool

# Executar pipeline completo (envia pro Notion!)
curl -X POST http://localhost:8000/api/agents/prospector/manual \
  -H "Content-Type: application/json" \
  -d '{
    "cnpj": "52346129000150",
    "site": "https://climadiagnosticos.com.br/",
    "whatsapp": "(11) 99208-0886"
  }' | python -m json.tool

# Listar histórico
curl http://localhost:8000/api/agents/prospector/leads?limit=10 | python -m json.tool
```

## Como adicionar um novo agente

A estrutura é "data-driven" — pra adicionar um novo agente:

1. **Registrar no `app/api/registry.py`:**
   ```python
   Agent(
       slug="cobranca",
       name="Cobrança",
       description="...",
       icon="ti-cash",
       status="active", 
       order=20,
   ),
   ```

2. **Criar o router em `app/api/routers/cobranca.py`** (espelhando `prospector.py`):
   ```python
   router = APIRouter(prefix="/api/agents/cobranca", tags=["cobranca"])
   # endpoints específicos...
   ```

3. **Plugar no `app/api/main.py`:**
   ```python
   from app.api.routers import cobranca as cobranca_router
   app.include_router(cobranca_router.router)
   ```

4. **Atualizar capabilities/status no registry quando estiver pronto.**

O frontend descobre o agente sozinho via `GET /api/agents` — não precisa
mexer em nada lá pra ele aparecer na sidebar.

## Estrutura

```
app/api/
├── main.py                       FastAPI app + CORS + roteamento
├── registry.py                   Registro central dos agentes
├── routers/
│   ├── agents.py                 GET /api/agents (list + detail)
│   └── prospector.py             Endpoints do Prospector
├── schemas/
│   └── prospector.py             Pydantic models (request/response)
└── services/
    ├── prospector_service.py     Orquestra o pipeline existente
    └── leads_reader.py           Lê data/sent/*.json pro histórico
```

**Camadas:** rotas → services → pipeline. Trocar o pipeline depois
mexe só em `services/`, não nas rotas.

## CORS

Liberado pra `http://localhost:3000` e `http://127.0.0.1:3000` (frontend Next.js
em dev). Pra produção, edite `app/api/main.py` e adicione o domínio real.

## Por que o histórico lê arquivo local em vez do Notion?

- Sem rate limit
- Sem latência (a tela carrega instantaneamente)
- Funciona offline
- O pipeline já salva tudo em `data/sent/*.json` automaticamente

O Notion é fonte de verdade pra negócio; o backup local é fonte de
verdade pra histórico operacional.
