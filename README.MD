# Prospector — Agente de Prospecção Automatizada

Agente que coleta dados públicos de empresas (Google Maps, BrasilAPI, sites)
e cadastra automaticamente no seu CRM Notion, com análise crítica gerada por IA.

## Estado atual: Fase 1 — Integração com Notion

Apenas a integração com o Notion está implementada. As demais fases virão
incrementalmente:

- ✅ **Fase 1** — Notion exporter + modelo Lead
- ⏳ Fase 2 — Modelo de dados (já dentro da F1)
- ⏳ Fase 3 — BrasilAPI (CNPJ, sócios, capital social)
- ⏳ Fase 4 — Storage local (já dentro da F1)
- ⏳ Fase 5 — Rate limiter
- ⏳ Fase 6 — Scraper de sites (e-mail, IG, FB, WhatsApp)
- ⏳ Fase 7 — Google Maps com Playwright
- ⏳ Fase 8 — Análise crítica com Gemini
- ⏳ Fase 9 — Orquestração (pipeline completo)
- ⏳ Fase 10 — FastAPI
- ⏳ Fase 11 — Frontend React

## Como rodar (Fase 1)

### 1. Pré-requisitos

- Python 3.10+
- Uma integração criada no Notion com permissão no database de Empresas e Contatos

### 2. Setup

```bash
# 1. Crie o ambiente virtual
python -m venv venv

# 2. Ative
# Linux/Mac:
source venv/bin/activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis
cp .env.example .env
# Edite .env e preencha NOTION_TOKEN, NOTION_DB_EMPRESAS, NOTION_DB_CONTATOS
```

### 3. Teste a integração com o Notion

```bash
python run.py test-notion
```

Esse comando cria uma empresa e um contato de teste no seu CRM. Vá lá conferir!
Se aparecer corretamente, a Fase 1 está validada. 

### 4. Comandos úteis

```bash
python run.py list-leads      # lista leads salvos localmente
```

## Estrutura de pastas

```
backend/
├── app/
│   ├── config.py            # carrega .env e define opções dos selects
│   ├── collectors/          # (próximas fases) Maps, BrasilAPI, sites
│   ├── analyzers/           # (Fase 8) análise crítica com Gemini
│   ├── exporters/           # notion_exporter.py
│   ├── models/              # lead.py — Empresa, Contato, Lead
│   ├── services/            # (próximas fases) orquestração
│   └── utils/               # logger, storage
├── data/
│   ├── raw/                 # JSONs brutos
│   ├── processed/           # leads prontos pra revisar
│   └── sent/                # leads já enviados pro Notion
├── logs/
├── .env                     # NUNCA commitar
├── requirements.txt
└── run.py                   # ponto de entrada
```

## Princípios do projeto

- **Lento de propósito**: delays aleatórios, no máximo 30-50 leads/dia
- **Idempotente**: salva tudo em JSON antes de enviar; não duplica empresas (busca por CNPJ)
- **Validação rígida**: opções de seleção do Notion não são criadas automaticamente
- **Logs claros**: tudo em `logs/prospector_YYYY-MM-DD.log`
- **Modular**: cada fase é um módulo independente
