# Frontend — Reativa Plataforma de Agentes (COMPLETO)

Dashboard Next.js 14 + TypeScript + Tailwind com o design system da Reativa
nativo, consumindo a API FastAPI do backend.

## 🚀 Setup e primeiro uso

```bash
# Estrutura do monorepo:
# prospector/
# ├── backend/                    ← já existe
# └── frontend/                   ← essa pasta

# 1. Instalar deps (uma vez)
cd frontend
npm install

# 2. Criar .env.local
cp .env.local.example .env.local

# 3. Subir o backend (em outro terminal)
cd ../backend
python run.py serve            # roda em http://localhost:8000

# 4. Subir o frontend
cd ../frontend
npm run dev                    # roda em http://localhost:3000

# Abre o navegador em http://localhost:3000
# Vai redirecionar pra /agents/prospector
```

## ✅ O que foi validado

| Checkpoint | Resultado |
|---|---|
| TypeScript estrito sem erros | ✅ 0 erros |
| Build de produção (`npm run build`) | ✅ 3/3 páginas geradas |
| Cliente HTTP fala com API real | ✅ 7/7 endpoints |
| Cores OKLCH da Reativa no CSS final | ✅ Aplicadas |
| Logo SVG idêntica ao site | ✅ |
| Fontes (Space Grotesk + Manrope + JetBrains Mono) | ✅ Preconnect otimizado |
| CORS pro localhost:3000 | ✅ |

## 🎯 Como adicionar um novo agente

A arquitetura é "data-driven" — pra adicionar um novo agente:

**1. Backend** — anexa no `app/api/registry.py`:
```python
Agent(slug="cobranca", name="Cobrança", icon="ti-cash",
      status="active", order=20, ...),
```

**2. Backend** — cria o router em `app/api/routers/cobranca.py`

**3. Backend** — plugue no `main.py`:
```python
from app.api.routers import cobranca as cobranca_router
app.include_router(cobranca_router.router)
```

**4. Frontend** — no `pages/agents/[slug].tsx`, adicione o branch:
```tsx
{agent.slug === 'prospector' ? <ProspectorScreen ... />
 : agent.slug === 'cobranca' ? <CobrancaScreen ... />
 : <ComingSoonScreen ... />}
```

**Nada mais.** Sidebar descobre sozinho. Sem nova rota.

## 🎨 Design system Reativa

Todas as cores OKLCH, fontes e radii do `styles.css` original viraram
utilitários Tailwind. No JSX:

```tsx
// Cores
<button className="bg-brand text-white shadow-brand-sm">       {/* CTA principal */}
<div className="bg-brand-soft text-brand-ink">                  {/* highlight */}
<p className="text-ink-mute">                                   {/* texto auxiliar */}

// Fontes
<h1 className="font-display tracking-tighter">                  {/* Space Grotesk */}
<span className="font-mono">                                    {/* JetBrains Mono */}

// Componentes prontos (em globals.css)
<button className="btn-primary">Prospectar</button>
<span className="eyebrow">Agente 01</span>
<div className="card p-6">...</div>
<input className="input" />
```

## 🔌 Funcionalidades já funcionando

- ✅ **Sidebar dinâmica** — lista agentes vindos do `GET /api/agents`
- ✅ **Formulário do Prospector** com 9 campos (CNPJ + site + 7 overrides)
- ✅ **Preview** — botão "Pré-visualizar" chama `POST /preview` (~2-5s)
- ✅ **Run** — botão "Prospectar e enviar" chama `POST /manual` (30s-2min)
- ✅ **Histórico** — lista os últimos 20 leads do backup local
- ✅ **Refetch automático** — após criar lead, lista atualiza sozinha
- ✅ **Tratamento de erro** — mensagens amigáveis do backend
- ✅ **Loading states** — skeleton, spinner, pipeline pill animado
- ✅ **Cancelamento de requisições** — AbortController em todas as mutações
- ✅ **Telas "em breve"** — pros 3 agentes do roadmap

## ⚠️ Limitações conhecidas

- Sem autenticação (estamos rodando local). Pra produção, adicione middleware Next + token Bearer.
- Histórico lê do backup local do backend (`data/sent/*.json`), não do Notion. Funciona offline, mas pode divergir se você editar manualmente no Notion.
- "Métricas" e "Conexões" são placeholders disabled pra evolução futura.

## 🔜 Próximos passos sugeridos

1. **Página de detalhe do Lead** — clicar numa linha abre `/agents/prospector/leads/[arquivo]`
2. **Filtros no histórico** — por setor, cidade, fonte
3. **Tela de Métricas** — gráfico de leads por dia, taxa de uso por fonte
4. **Tela de Conexões** — gerenciar tokens sem mexer no `.env`
5. **Toast de notificação** — feedback visual quando lead é criado/falha
6. **Dark mode** — toggle no topbar
