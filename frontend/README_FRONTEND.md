# Frontend — Plataforma de Agentes da Reativa

Dashboard Next.js 14 + TypeScript + Tailwind, com o design system da Reativa nativo, consumindo a API FastAPI do backend.

> Pra visão geral do projeto inteiro, veja [`../README.md`](../README.md).

---

## Quickstart

```bash
# Da raiz do monorepo
cd frontend

# 1. Instala deps (uma vez só)
npm install

# 2. Configura URL da API
cp .env.local.example .env.local
# Default: NEXT_PUBLIC_API_URL=http://localhost:8000 (mexa só se mudar a porta)

# 3. Garanta que o backend está rodando em outro terminal:
#    cd ../backend && python run.py serve

# 4. Sobe o frontend
npm run dev
```

Pronto. Abre **http://localhost:3000** — redireciona pra `/agents/prospector`.

---

## Estrutura

```
frontend/
├── package.json
├── tsconfig.json                  ← TypeScript strict, paths @/...
├── tailwind.config.ts             ← Design system Reativa (OKLCH) ⭐
├── postcss.config.js
├── next.config.js
├── .env.local.example
│
├── styles/
│   └── globals.css                ← Base + componentes (.eyebrow, .btn-primary, etc.)
│
├── lib/                           ← Camada de dados
│   ├── api.ts                     ← Cliente HTTP tipado (fala com FastAPI)
│   ├── types.ts                   ← Tipos espelhando schemas Pydantic
│   └── format.ts                  ← Helpers (formatCnpj, etc.)
│
├── hooks/                         ← React hooks
│   ├── useFetch.ts                ← Hook genérico (loading/erro/dados)
│   ├── useAgents.ts               ← Lista agentes da plataforma
│   └── useProspector.ts           ← preview/run/histórico
│
├── components/                    ← Componentes reutilizáveis
│   ├── BrandMark.tsx              ← Logo SVG da Reativa
│   ├── Icon.tsx                   ← Ícones inline (sem dep externa)
│   ├── DashboardLayout.tsx        ← Wrapper sidebar + topbar + content
│   ├── Sidebar.tsx                ← Menu lateral dinâmico
│   ├── Topbar.tsx                 ← Breadcrumb + ações
│   ├── StatCard.tsx               ← Card de métrica
│   ├── LeadRow.tsx                ← Linha do histórico + lista
│   ├── ProspectorForm.tsx         ← Formulário completo do Prospector
│   └── MoreAgentsSection.tsx      ← Cards "em breve" pros próximos agentes
│
└── pages/
    ├── _app.tsx                   ← Wrapper global (importa Tailwind)
    ├── _document.tsx              ← <head> + Google Fonts (preconnect)
    ├── index.tsx                  ← Redirect → /agents/prospector
    └── agents/
        └── [slug].tsx             ← Tela dinâmica de qualquer agente ⭐
```

⭐ = arquivos-chave da arquitetura

---

## Design system da Reativa

Todas as cores OKLCH, fontes e radii do site principal (`styles.css`) viraram **utilitários Tailwind**. Você escreve `bg-brand text-ink-mute` e renderiza idêntico ao site.

### Cores

```tsx
// Marca (laranja)
<button className="bg-brand text-white">Prospectar</button>
<div className="bg-brand-soft text-brand-ink">Highlight</div>
<div className="bg-brand-deep">Hover do CTA</div>

// Neutros (warm)
<div className="bg-bg">                     {/* fundo padrão */}
<div className="bg-bg-alt">                 {/* fundo secundário */}
<div className="bg-surface border border-line">  {/* card */}
<p className="text-ink">                    {/* texto principal */}
<p className="text-ink-soft">               {/* texto secundário */}
<p className="text-ink-mute">               {/* texto auxiliar */}
<p className="text-ink-faint">              {/* texto desativado */}

// Semânticas
<span className="text-success bg-success-soft">OK</span>
```

### Fontes

```tsx
<h1 className="font-display tracking-tighter">    {/* Space Grotesk */}
<p className="font-body">                          {/* Manrope (default) */}
<code className="font-mono">                       {/* JetBrains Mono */}
<span className="text-eyebrow">                    {/* tamanho específico */}
```

### Componentes prontos (em `globals.css`)

```tsx
<button className="btn-primary">           {/* CTA pill laranja com glow */}
<button className="btn-ghost">             {/* botão secundário */}
<span className="eyebrow">                 {/* label monospaced com risco */}
<div className="card p-6">                 {/* superfície branca com borda */}
<input className="input" />                {/* input padrão com focus laranja */}
```

### Sombras

```tsx
<div className="shadow-sm">                 {/* sutil */}
<div className="shadow">                    {/* card padrão */}
<div className="shadow-lg">                 {/* elevação alta */}
<div className="shadow-brand-sm">           {/* glow laranja pequeno */}
<div className="shadow-brand">              {/* glow laranja maior */}
<div className="shadow-focus">              {/* anel de focus laranja */}
```

### Onde isso é definido

Tudo configurado em `tailwind.config.ts`. Se quiser adicionar uma cor nova, edite lá — vira utilitário automaticamente.

---

## Camada de dados — `lib/api.ts` e hooks

### Como usar (em qualquer componente)

```tsx
import { useAgents } from '@/hooks/useAgents';
import { useProspectorPreview, useProspectorHistory } from '@/hooks/useProspector';

function MinhaTela() {
  // Auto-fetcha no mount, atualiza em cada render
  const { agents, loading, error } = useAgents();

  // Histórico de leads
  const history = useProspectorHistory(20);

  // Mutação manual — não executa sozinha
  const preview = useProspectorPreview();

  async function handleClick() {
    await preview.execute({
      cnpj: '52346129000150',
      site: 'https://exemplo.com.br',
      whatsapp: '(11) 99999-9999',
    });
    if (preview.data) {
      console.log('Lead:', preview.data.lead.empresa.nome);
    }
  }

  // Tratamento de erro tipado
  if (preview.error?.isClientError) {
    return <div>Erro do usuário: {preview.error.message}</div>;
  }
  if (preview.error?.isServerError) {
    return <div>Erro do servidor — tenta de novo daqui a pouco</div>;
  }
}
```

### Configuração do client

- **Timeout** — 60s no `/preview`, 3min no `/manual` (pipeline IA pode demorar)
- **AbortController** — cada chamada cancela a anterior se em flight
- **Erro padronizado** — `ApiError` com `status`, `detail`, `isClientError`, `isServerError`
- **JSON automático** — request/response sempre tipados

### Endpoints disponíveis (em `lib/api.ts`)

```ts
api.healthcheck()                    // GET /api/health
api.listAgents()                     // GET /api/agents
api.getAgent(slug)                   // GET /api/agents/{slug}
api.prospectorPreview(body)          // POST /api/agents/prospector/preview
api.prospectorRun(body)              // POST /api/agents/prospector/manual
api.prospectorHistory(limit)         // GET /api/agents/prospector/leads
```

---

## Como adicionar um novo agente

A página `pages/agents/[slug].tsx` aceita **qualquer slug** que o backend declarar. Pra dar uma tela própria ao agente novo:

### 1. Cria o componente da tela

`components/CobrancaScreen.tsx`:
```tsx
export function CobrancaScreen() {
  // copie ProspectorScreen e adapte os campos
  return (
    <div className="max-w-[1200px] mx-auto">
      <header className="mb-7">
        <div className="eyebrow mb-3">Agente · Cobrança</div>
        <h1 className="font-display ...">Cobrança</h1>
        ...
      </header>
      <CobrancaForm />
      ...
    </div>
  );
}
```

### 2. Liga a tela no `pages/agents/[slug].tsx`

```tsx
{agent.slug === 'prospector' ? <ProspectorScreen agents={agents} />
 : agent.slug === 'cobranca' ? <CobrancaScreen />
 : <ComingSoonScreen agentName={agent.name} />}
```

### 3. (Se precisar) Cria hook próprio

`hooks/useCobranca.ts` espelhando `useProspector.ts`.

Pronto. **Não precisa**:
- Criar nova rota (a `[slug].tsx` cobre)
- Mexer na sidebar (descobre sozinha via `useAgents`)
- Mexer no roteamento (já é dinâmico)

---

## Funcionalidades implementadas

| Funcionalidade | Status |
|---|---|
| Sidebar dinâmica (vem do backend) | ✅ |
| Formulário Prospector com 9 campos | ✅ |
| Botão "Pré-visualizar" (`POST /preview`) | ✅ |
| Botão "Prospectar e enviar" (`POST /manual`) | ✅ |
| Painel de preview do Lead montado | ✅ |
| Histórico dos últimos 20 leads | ✅ |
| Refetch automático após criar lead | ✅ |
| Erro inline com botão de dispensar | ✅ |
| Sucesso inline com resumo | ✅ |
| Loading states (skeleton, spinner, pipeline pulsando) | ✅ |
| Cancelamento via AbortController | ✅ |
| Telas "em breve" pros outros agentes | ✅ |
| Máscara progressiva de CNPJ no input | ✅ |
| Ícones inline (sem dep externa) | ✅ |
| Cores OKLCH idênticas ao site principal | ✅ |
| Fontes Google com preconnect otimizado | ✅ |


## Troubleshooting

### "Não está lincado" / sidebar fica em "Carregando…"

```bash
# 1. Confirma que o backend está rodando
curl http://localhost:8000/api/health
# Esperado: {"status":"ok","service":"reativa-agents-api"}

# Se der "Connection refused", suba o backend:
cd ../backend && source venv/bin/activate && python run.py serve
```

### Console do navegador mostra erro de CORS

CORS no backend libera só `localhost:3000`. Se você estiver rodando o front em outra porta, **edite `backend/app/api/main.py`** e adicione na lista `allow_origins`.

### `npm run build` falha com erro de tipo

```bash
npm run typecheck
# Mostra todos os erros TS sem fazer build
```

Erros comuns:
- Esqueceu de tipar prop de componente → adiciona interface
- Acessou `.empresa.nome` quando `empresa: Empresa | null` → use `?.` ou guard

### Cores não aparecem (tudo cinza)

Confira se `globals.css` está sendo importado no `pages/_app.tsx`:
```tsx
import '@/styles/globals.css';
```

E confira se `tailwind.config.ts` aponta pra suas pastas em `content`:
```ts
content: [
  './pages/**/*.{ts,tsx}',
  './components/**/*.{ts,tsx}',
  './lib/**/*.{ts,tsx}',
  './hooks/**/*.{ts,tsx}',
],
```

---

##  Roadmap

- [ ] Página de detalhe do Lead (clicar numa linha do histórico)
- [ ] Filtros no histórico (setor, fonte, data)
- [ ] Tela de Métricas (gráfico de leads/dia, fontes usadas)
- [ ] Tela de Conexões (gerenciar tokens sem mexer no `.env`)
- [ ] Toast de notificação no canto da tela
- [ ] Dark mode com toggle no topbar
- [ ] Importação CSV em lote
- [ ] Tab "Investigar" funcionando (modo descoberta por nome)
- [ ] Auth real (NextAuth)
- [ ] Deploy na Vercel

---

## Stack

| Camada | Tecnologia |
|---|---|
| Framework | Next.js 14 (Pages Router) |
| Linguagem | TypeScript 5 strict |
| UI | React 18 |
| Estilos | Tailwind CSS 3.4 + design system Reativa |
| Fontes | Google Fonts (Space Grotesk + Manrope + JetBrains Mono) |
| HTTP | `fetch` nativo (zero deps) |
| Ícones | Inline SVG (zero deps) |