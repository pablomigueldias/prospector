# Prospector

Agente de prospecção automatizada que coleta dados públicos de empresas brasileiras
e cadastra no Notion CRM com análise crítica gerada por IA — pronta pra
pré-apresentação.

```
CNPJ + Site → BrasilAPI + Scraping + Gemini → Notion CRM
```

**Status atual:** funcional via CLI, em fase de teste manual.

---

## Comandos disponíveis

### Pipeline completo (o que vai usar 90% das vezes)

```bash
python run.py prospectar-full <CNPJ> [URL_DO_SITE]
```

Faz tudo de uma vez:
1. Busca CNPJ na BrasilAPI (razão social, capital, sócios, CNAE, endereço)
2. Acessa o site da empresa (se passado) e extrai email, WhatsApp, Instagram, Facebook
3. Roda análise crítica com Gemini (score, dores, ganchos de venda, perguntas pra call)
4. Cadastra Empresa + Contato(s) no Notion CRM com tudo formatado

**Exemplo:**
```bash
python run.py prospectar-full 40165696000120 https://exemplo.com.br
```

### Comandos individuais (debug e granularidade)

| Comando | O que faz |
|---|---|
| `python run.py test-conexao` | Testa se Notion API responde |
| `python run.py test-notion` | Cria empresa/contato fake (validar Notion) |
| `python run.py buscar-cnpj <CNPJ>` | Mostra dados da BrasilAPI no terminal (não cadastra) |
| `python run.py extrair-site <URL>` | Lista contatos achados no site |
| `python run.py extrair-site <URL> --playwright` | Mesma coisa, mas força JS (sites WordPress complexos) |
| `python run.py analisar-cnpj <CNPJ> [URL]` | Roda só a análise IA, mostra no terminal |
| `python run.py prospectar-cnpj <CNPJ>` | CNPJ → Notion (sem site, sem IA) |
| `python run.py prospectar-completo <CNPJ> [URL]` | CNPJ + site → Notion (sem IA) |
| `python run.py list-leads` | Lista arquivos JSON de leads salvos |

---

## Estrutura do projeto

```
prospector/backend/
├── run.py                          # ponto de entrada (todos os comandos)
├── requirements.txt
├── .env                            # chaves
├── .env.example                    # template
│
├── app/
│   ├── config.py                   # carrega .env + opções dos selects
│   ├── models/lead.py              # Empresa, Contato, Lead, Socio (Pydantic)
│   │
│   ├── collectors/
│   │   ├── brasilapi/              # CNPJ → Empresa
│   │   │   ├── client.py           # chamada HTTP com retry
│   │   │   ├── mappers.py          # JSON → Empresa + Contatos
│   │   │   └── classifiers.py      # CNAE→Setor, capital→Tamanho
│   │   │
│   │   └── website/                # URL → contatos
│   │       ├── client.py           # httpx + fallback Playwright
│   │       ├── stealth.py          # anti-detecção
│   │       ├── extractors.py       # regex email/tel/whats/redes
│   │       ├── crawler.py          # decide quais páginas visitar
│   │       └── cache.py            # cache 7 dias
│   │
│   ├── analyzers/
│   │   └── gemini/                 # IA → análise crítica
│   │       ├── client.py           # API do Gemini
│   │       ├── prompt_builder.py   # constrói prompt rico
│   │       └── parser.py           # JSON → AnaliseGemini (com reparo)
│   │
│   ├── exporters/
│   │   └── notion/                 # Lead → Notion CRM
│   │       ├── exporter.py         # orquestrador
│   │       ├── repository.py       # find / create / update
│   │       ├── mappers.py          # Empresa → propriedades Notion
│   │       └── property_builder.py # JSON da API Notion por tipo
│   │
│   └── utils/
│       ├── logger.py               # loguru (console + arquivo)
│       └── storage.py              # leads em JSON local
│
├── data/
│   ├── raw/                        # JSONs crus (antes de processar)
│   ├── processed/                  # leads prontos pra revisar
│   ├── sent/                       # leads já enviados pro Notion
│   ├── cache/website/              # HTML cacheado (7 dias)
│   ├── debug/gemini/               # respostas crus se IA falhar
│   └── unmapped_fields.json        # valores que não bateram com select
│
└── logs/
    └── prospector_YYYY-MM-DD.log   # log diário (7 dias de retenção)
```

---

## Instalação

```bash
# 1. Cria ambiente virtual
python -m venv venv

# 2. Ativa
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

# 3. Instala dependências
pip install -r requirements.txt

# 4. Instala o navegador do Playwright
playwright install chromium

# 5. Configura .env
cp .env.example .env
# edita .env com as chaves reais
```

---

## 🔑 Configuração do .env

```env
# --- Notion ---
NOTION_TOKEN=ntn_seu_token_aqui
NOTION_DB_EMPRESAS= Seu codigo aqui
NOTION_DB_CONTATOS= Seu codigo aqui

# --- Gemini ---
GEMINI_API_KEY=AIza_sua_chave_aqui

# --- Rate Limiting (proteção anti-bloqueio em scraping) ---
MAX_LEADS_PER_DAY=30
MIN_DELAY_SECONDS=5
MAX_DELAY_SECONDS=15

# --- Comportamento ---
LOG_LEVEL=INFO
HEADLESS_BROWSER=false
```

### Onde pegar cada chave

| Chave | Onde pegar |
|---|---|
| `NOTION_TOKEN` | notion.so/profile/integrations → Sua integração "Prospect" → Token |
| `NOTION_DB_EMPRESAS` / `NOTION_DB_CONTATOS` | URL do database no Notion (os 32 caracteres antes do `?v=`) |
| `GEMINI_API_KEY` | aistudio.google.com/apikey → "Create API key" |

---

## O que vai pro Notion

### Empresa (database "Empresas")
- Nome, Razão Social, CNPJ formatado
- Capital Social (R$)
- Cidade, Estado (select), Endereço completo
- Setor (mapeado do CNAE)
- Tamanho (estimado por porte + capital)
- Site, Instagram, Facebook
- Sócios (texto único separado por vírgula)
- Status: 🔵 Prospect (default)
- Como conheceu: Outbound (default)
- **Notas:** observações da BrasilAPI + extras do site + **análise da IA**

### Contato (database "Contatos")
- Nome (sócio ou "Empresa - Contato Comercial")
- Cargo, Decisor? (Sim/Não)
- E-mail, Telefone, WhatsApp, LinkedIn
- Vinculado à Empresa via relação
- Origem do contato: Network (default)

### Notas da IA (exemplo real)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 ANÁLISE IA  |  ⚠️ Score: 45/100
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Empresa individual de advocacia sem presença digital...

📋 RESUMO
Escritório jurídico em Atibaia sem nenhuma presença digital...

🏢 PERFIL
Porte: Pequena sociedade individual de advocacia.

⚡ DORES PROVÁVEIS
1. Dificuldade em atrair novos clientes online
   ↳ Ausência total de site e redes sociais
2. Processos manuais de gestão de casos
   ↳ Suposição (padrão do setor)

💡 GANCHOS DE VENDA
1. Site institucional profissional
2. CRM jurídico básico

❓ PERGUNTAS PRA CALL
1. Como vocês atraem novos clientes hoje?
2. Como organizam processos dos clientes?

🚨 ALERTAS
• Capital baixo (R$ 10k) — orçamento limitado
• Empresa unipessoal — sócio único é o decisor
```

---

##  Como o agente decide as coisas

### Idempotência (não duplica)
- **Empresa:** busca por CNPJ formatado no Notion antes de criar. Se existir, atualiza.
- **Contato:** busca por (email na mesma empresa) → fallback (nome na mesma empresa).

### Validação de selects
- Nunca cria opção nova de Setor/Tamanho/etc. automaticamente.
- Valores não mapeados vão pra `data/unmapped_fields.json` pra revisar.
- Estratégia: ou adiciona a opção manualmente no Notion, ou aceita campo vazio.

### Mapeamento CNAE → Setor (BrasilAPI)
| Divisão CNAE | Setor |
|---|---|
| 62, 63, 61 | Tech |
| 47, 46, 45 | Varejo |
| 86, 87, 88 | Saúde |
| 85 | Educação |
| 69 | Jurídico |
| 64-66 | Financeiro |
| 41-43, 68 | Imobiliário |
| 73, 58-60 | Marketing |
| 10-33 | Indústria |
| outros | Serviços ou vazio |

### Tamanho (porte + capital social)
- Porte=MEI → MEI
- Porte=ME ou capital ≤ R$ 360k → Pequena (1-10)
- Porte=EPP ou capital ≤ R$ 4,8M → Média (11-50)
- Capital ≤ R$ 50M → Grande (51-200)
- Capital > R$ 50M → Corporativa (200+)

### Telefone vs WhatsApp
- **wa.me / api.whatsapp.com** → sempre WhatsApp (override)
- **Celular** (11 dígitos, 9 inicial) → WhatsApp por default
- **Fixo** (10 dígitos, começa com 2-5) → Telefone
- **"Telefone:"** explícito no contexto → força pra Telefone
- DDDs inválidos (não existem na Anatel) → ignorados

### Quando o site é JS-pesado (SPA)
- Tenta httpx primeiro (rápido, 1-3s)
- Se vier vazio / HTML pequeno / muitos scripts → escala automático pra Playwright (lento, 8-15s)
- Pode forçar Playwright direto com `--playwright`

---

##  Troubleshooting

### "GEMINI_API_KEY não está no .env"
Pega chave grátis em https://aistudio.google.com/apikey e adiciona no `.env`.

### "unauthorized" no Notion
- Confere o `NOTION_TOKEN` no `.env`
- Confere se a integração "Prospect" está conectada ao CRM Reativa
  (no Notion: abrir página → menu lateral direito → Conexões)

### "Modelo gemini-2.5-flash não encontrado"
Google trocou o nome. Edita `app/analyzers/gemini/client.py`, troca `MODEL` pelo modelo atual.
Lista de modelos: https://ai.google.dev/gemini-api/docs/models

### Cache atrapalhando teste
```bash
rm data/cache/website/*.json
```

### Site não responde / DNS inválido
O agente detecta e aborta em 2-3s (`DominioInvalido`). Confere se a URL tá certa.

### Texto longo demais pra um campo do Notion
Já tem proteção: rich_text é quebrado em pedaços <= 2000 chars. Title é truncado com "...".

### Quando preciso revisar manualmente?
- `data/unmapped_fields.json` — valores que não bateram com selects do Notion
- `data/debug/gemini/` — respostas que a IA enviou e o parser não conseguiu processar
- Estado da empresa fora de SP/RJ/MG/RS/PR/SC/BA/DF — vai vazio + warning

---

## Boas práticas pra não tomar bloqueio

1. **Limite-se a 30-50 leads por dia** (configurável em `MAX_LEADS_PER_DAY`)
2. **Não rode múltiplas prospecções em paralelo** no mesmo dia
3. Se tomar `403`/`429` muito → para por 24-48h
4. **Não scrape Instagram/Facebook diretamente** — só pega os LINKS que aparecem no site
5. Cache de 7 dias evita re-baixar o mesmo site
6. Delay aleatório entre páginas (3-7s)

---

## Próximas fases planejadas

- ⏳ **Fase 7 — Google Maps**: buscar por "pizzarias em Santo André" e descobrir CNPJs automaticamente
- ⏳ **Fase 10 — FastAPI**: expor o agente via API REST
- ⏳ **Fase 11 — Frontend React**: interface web com formulário e tabela
- ⏳ **Fase 5 — Rate limiter global**: centralizar controle de volume (necessário pra Fase 7)

