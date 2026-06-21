# Guia detalhado — Página `/projetos` no `reativesystems.com.br`

> **Objetivo:** transformar o site institucional em **prova viva**. Criar a página
> `/projetos` com 3–4 casos no formato que cliente entende
> (**Problema → Solução → Stack → Resultado**), com print/GIF, botões
> *Ver ao vivo* + *Código*, e um CTA final.
>
> Este guia foi escrito olhando o repositório **real** `reative-site`
> (Next.js 14 App Router, **TypeScript**, **CSS puro com tokens** — *não* Tailwind).
> Os caminhos, imports e convenções abaixo são os que o projeto já usa.

---

## 0. Antes de começar — o terreno (já confirmado no repo)

| Item | Como é no `reative-site` |
|---|---|
| Framework | Next.js **14.2** com **App Router** (`app/`) |
| Linguagem | **TypeScript** (`.tsx`), componentes retornam `JSX.Element` |
| Estilo | **CSS puro** em `app/styles/` com **tokens** (`var(--brand)`, etc.). Cada seção tem seu `.css` registrado em `app/globals.css` via `@import`. **Não tem Tailwind.** |
| Conteúdo | Separado em `lib/content/*.ts`, tipado por `lib/types.ts` |
| Destaque de texto | Sintaxe `[[texto]]` → `renderAccented()` de `lib/text.tsx` vira `<span class="accent">` |
| Ícones | `RenderIcon name={iconKey}` e `Icon.ArrowUpRight` de `components/ui/Icon.tsx` |
| Páginas estáticas | `app/<rota>/page.tsx` com `export const metadata` + componente |
| Nav | `components/layout/Nav.tsx`; em páginas que **não** são a home use `<Nav external />` |
| Config/CTA | `lib/config.ts` → `config.contact`, `whatsappUrl(msg)`, `config.site.url` |

> ⚠️ **Atenção:** você lembrava como Tailwind, mas o repo é CSS com tokens. O guia
> segue o CSS (é o que cola). Se você migrou pra Tailwind depois, me avisa que
> reescrevo os blocos de estilo.

**Decisão deste guia:** página dedicada em `/projetos` (rota própria), igual o
plano (`Plano-Entrar-no-Jogo.md` §2.1). No fim tem um passo opcional pra colocar
um *teaser* de 1 projeto na home.

**Arquivos que você vai criar/editar (mapa):**

```
reative-site/
├─ lib/
│  ├─ types.ts                      ← EDITAR  (+ tipo Projeto)
│  └─ content/
│     └─ projetos.ts                ← CRIAR   (os 3–4 casos)
├─ components/sections/
│  └─ Projetos.tsx                  ← CRIAR   (grid + cards)
├─ app/
│  ├─ projetos/
│  │  └─ page.tsx                   ← CRIAR   (rota /projetos + SEO)
│  ├─ globals.css                   ← EDITAR  (+ @import do css novo)
│  └─ styles/sections/
│     └─ projetos.css               ← CRIAR   (estilo)
├─ components/layout/Nav.tsx        ← EDITAR  (+ link "Projetos")
└─ public/projetos/                 ← CRIAR   (prints/gifs)
```

---

## 1. Como a página vai ficar (wireframe)

```
┌─────────────────────────────────────────────────────────┐
│  NAV (Projetos em destaque)                               │
├─────────────────────────────────────────────────────────┤
│  eyebrow: PROJETOS                                        │
│  H2: Coisas que eu construí — e estão [[no ar]].          │
│  lede: 1 parágrafo (cliente vê produto real, não promessa)│
├─────────────────────────────────────────────────────────┤
│  ┌── CARD FEATURED (Reative Studio) ──────────────────┐  │
│  │  [print/gif do produto]                            │  │
│  │  eyebrow · título                                  │  │
│  │  Problema / Solução                                │  │
│  │  [chips de stack]                                  │  │
│  │  ✓ Resultado em destaque                           │  │
│  │  [ Ver ao vivo ↗ ]  [ Código (GitHub) ]            │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌── card ──┐ ┌── card ──┐   (Content Factory, Churn)     │
│  │  ...     │ │  ...     │                                │
│  └──────────┘ └──────────┘                                │
├─────────────────────────────────────────────────────────┤
│  CTA: "Precisa de algo assim? Fale comigo" → WhatsApp     │
├─────────────────────────────────────────────────────────┤
│  FOOTER                                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Passo 1 — Tipo `Projeto` (`lib/types.ts`)

Adicione no fim do arquivo (perto dos outros blocos `// ===`):

```ts
// ============================================
// Projetos (portfólio / casos)
// ============================================

export interface Projeto {
  /** slug pra âncora/id (ex.: "reative-studio") */
  slug: string;
  /** nome do projeto (ex.: "Reative Studio") */
  name: string;
  /** texto curto acima do título — ex.: "SaaS · IA · em produção" */
  eyebrow: string;
  /** frase-título com markers [[...]] pra destaque */
  tagline: string;
  /** o que o cliente sofria / o contexto */
  problem: string;
  /** o que foi construído pra resolver */
  solution: string;
  /** tecnologias (viram chips) */
  stack: string[];
  /** resultado/uso com marker [[...]] — ex.: "[[em produção]] com 2FA e bot" */
  result: string;
  /** link "ver ao vivo" (opcional) */
  liveUrl?: string;
  /** link do repositório no GitHub (opcional) */
  repoUrl?: string;
  /** caminho do print/gif em /public (ex.: "/projetos/studio.png") */
  shot?: string;
  /** destaca o card (ocupa a largura toda no topo) */
  featured?: boolean;
}
```

> Por que um tipo novo e não reusar `ServiceCase`: `ServiceCase` não tem
> `stack`, `liveUrl`, `repoUrl` nem `shot`. Projetos precisam disso.

---

## 3. Passo 2 — Conteúdo dos casos (`lib/content/projetos.ts`) **CRIAR**

Esse é o coração — texto puro, fácil de editar depois. Já vem **preenchido** com
seus projetos reais (ajuste números/links). Ordem de destaque conforme o plano.

```ts
import type { Projeto } from '@/lib/types';

/**
 * Casos do portfólio. Cada um no formato Problema → Solução → Stack → Resultado.
 * Texto entre [[...]] vira destaque (renderAccented). Edite à vontade —
 * é a fonte de verdade da página /projetos.
 */
export const projetos: Projeto[] = [
  {
    slug: 'reative-studio',
    name: 'Reative Studio (Prospector)',
    eyebrow: 'Plataforma SaaS · IA · em produção',
    tagline: 'Uma plataforma [[multiagente]] que trabalha sozinha.',
    problem:
      'Tarefas repetitivas de prospecção, finanças e candidatura tomavam horas e viviam espalhadas em planilhas e abas.',
    solution:
      'Construí uma plataforma web multiagente: cada agente resolve uma frente (vagas, freela, finanças, currículo ATS) usando IA, com login, 2FA, RBAC e bot de Telegram. Tudo em produção, atrás de HTTPS automático.',
    stack: [
      'Python', 'FastAPI', 'PostgreSQL', 'Alembic', 'Next.js', 'TypeScript',
      'Docker', 'Caddy', 'LLMs (Gemini/Groq)', 'Telegram Bot',
    ],
    result: 'No ar, [[com 2FA, RBAC e bot]], rodando 24/7 num VPS.',
    liveUrl: 'https://studio.reativesystems.com.br',
    repoUrl: 'https://github.com/pablomigueldias/prospector',
    shot: '/projetos/studio.png',
    featured: true,
  },
  {
    slug: 'content-factory',
    name: 'Content Factory',
    eyebrow: 'IA generativa · conteúdo',
    tagline: 'Geração de conteúdo com IA — [[texto e voz]].',
    problem:
      'Produzir conteúdo em escala (texto + áudio) consistente e rápido é caro e manual.',
    solution:
      'Backend orquestrado pra gerar conteúdo com IA: pipelines de texto, embeddings pra busca semântica e geração de voz, com foco em código limpo e testes automatizados.',
    stack: [
      'Python', 'FastAPI', 'PostgreSQL', 'google-genai',
      'sentence-transformers', 'pytest',
    ],
    result: 'Pipelines reaproveitáveis e [[testados]] de ponta a ponta.',
    repoUrl: 'https://github.com/pablomigueldias/content-factory', // ajuste o slug real
    shot: '/projetos/content-factory.png',
  },
  {
    slug: 'churn-prediction',
    name: 'Churn Prediction',
    eyebrow: 'Machine Learning · negócio',
    tagline: 'ML que prevê [[evasão de clientes]] antes de acontecer.',
    problem:
      'Empresas perdem clientes sem enxergar o risco a tempo de agir.',
    solution:
      'Modelo de Machine Learning que prevê evasão, servido por uma API em FastAPI — mostrando manipulação de dados e visão de negócio, não só código.',
    stack: ['Python', 'pandas', 'scikit-learn', 'FastAPI'],
    result: 'Da modelagem ao [[modelo servido em API]].',
    repoUrl: 'https://github.com/pablomigueldias/churn-prediction', // ajuste o slug real
    shot: '/projetos/churn.png',
  },
  // (opcional) 4º caso — Portfólio/Blog técnico, ou o próprio reative-site.
  // {
  //   slug: 'reative-site',
  //   name: 'Reative Site',
  //   eyebrow: 'Site institucional · Next.js',
  //   tagline: 'Site rápido, [[A+ no Lighthouse]] e fácil de manter.',
  //   problem: 'Precisava de presença profissional, veloz e editável.',
  //   solution: 'Site em Next.js 14 (App Router), CSS com tokens, SEO técnico e formulário de contato.',
  //   stack: ['Next.js', 'TypeScript', 'CSS', 'SEO técnico'],
  //   result: 'No ar em [[reativesystems.com.br]].',
  //   liveUrl: 'https://reativesystems.com.br',
  //   shot: '/projetos/site.png',
  // },
];
```

> **Confira os slugs do GitHub** (`content-factory`, `churn-prediction`): troque
> pelos nomes reais dos repositórios. Se um repo for privado, **deixe `repoUrl`
> de fora** (o botão some sozinho — ver Passo 4) e mantenha só *Ver ao vivo*.

---

## 4. Passo 3 — Componente da seção (`components/sections/Projetos.tsx`) **CRIAR**

Mesma estrutura das outras seções (`<section><div className="wrap">…`),
reusando classes existentes (`.wrap`, `.section-head`, `.eyebrow`, `.lede`).

```tsx
import { Icon } from '@/components/ui/Icon';
import { projetos } from '@/lib/content/projetos';
import { renderAccented } from '@/lib/text';
import type { Projeto } from '@/lib/types';

export function Projetos(): JSX.Element {
  return (
    <section id="projetos">
      <div className="wrap">
        <div className="section-head">
          <div>
            <span className="eyebrow">Projetos</span>
            <h2>Coisas que eu construí — e estão {renderAccented('[[no ar]]')}.</h2>
          </div>
          <p className="lede">
            Não é promessa: é produto real funcionando. Cada caso abaixo tem o
            problema, a solução, a stack e o resultado — e, quando dá, o link pra
            você ver ao vivo.
          </p>
        </div>

        <div className="projetos-grid">
          {projetos.map((p) => (
            <ProjetoCard key={p.slug} projeto={p} />
          ))}
        </div>
      </div>
    </section>
  );
}

function ProjetoCard({ projeto: p }: { projeto: Projeto }): JSX.Element {
  return (
    <article
      id={p.slug}
      className={p.featured ? 'projeto featured' : 'projeto'}
    >
      {p.shot && (
        <div className="projeto-shot">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={p.shot} alt={`Print do projeto ${p.name}`} loading="lazy" />
        </div>
      )}

      <div className="projeto-body">
        <span className="projeto-eyebrow">{p.eyebrow}</span>
        <h3>{p.name}</h3>
        <p className="projeto-tagline">{renderAccented(p.tagline)}</p>

        <dl className="projeto-ps">
          <dt>Problema</dt>
          <dd>{p.problem}</dd>
          <dt>Solução</dt>
          <dd>{p.solution}</dd>
        </dl>

        <div className="projeto-stack">
          {p.stack.map((t) => (
            <span className="projeto-chip" key={t}>{t}</span>
          ))}
        </div>

        <p className="projeto-result">✓ {renderAccented(p.result)}</p>

        <div className="projeto-actions">
          {p.liveUrl && (
            <a
              className="projeto-btn primary"
              href={p.liveUrl}
              target="_blank"
              rel="noopener noreferrer"
            >
              Ver ao vivo <Icon.ArrowUpRight width={16} height={16} />
            </a>
          )}
          {p.repoUrl && (
            <a
              className="projeto-btn ghost"
              href={p.repoUrl}
              target="_blank"
              rel="noopener noreferrer"
            >
              Código (GitHub)
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
```

> Os botões só aparecem se o link existir (`{p.liveUrl && …}`). Projeto sem live
> e sem repo simplesmente não mostra botão.

---

## 5. Passo 4 — A rota `/projetos` com SEO (`app/projetos/page.tsx`) **CRIAR**

Mesmo padrão de `app/privacidade/page.tsx`: `metadata` + componente, com `Nav`
e `Footer` (como a home monta). Use `<Nav external />` porque não é a home.

```tsx
import type { Metadata } from 'next';
import { Footer } from '@/components/layout/Footer';
import { Nav } from '@/components/layout/Nav';
import { Projetos } from '@/components/sections/Projetos';
import { ProjetosCta } from '@/components/sections/Projetos'; // ver Passo 8 (CTA)
import { config } from '@/lib/config';

export const metadata: Metadata = {
  title: 'Projetos — Reative Systems',
  description:
    'Casos reais construídos pela Reative Systems: plataforma multiagente com IA, geração de conteúdo e Machine Learning — em produção, com link pra ver ao vivo.',
  alternates: { canonical: `${config.site.url}/projetos` },
  openGraph: {
    title: 'Projetos — Reative Systems',
    description:
      'Produto real funcionando: IA, automação e ML em produção. Veja os casos.',
    url: `${config.site.url}/projetos`,
    type: 'website',
  },
};

export default function ProjetosPage(): JSX.Element {
  return (
    <>
      <Nav external />
      <main>
        <Projetos />
        <ProjetosCta />
      </main>
      <Footer />
    </>
  );
}
```

> Se você preferir **não** criar o `ProjetosCta` (Passo 8), remova as duas linhas
> que o referenciam e use a seção `<Contact />` existente no lugar.

---

## 6. Passo 5 — Estilos (`app/styles/sections/projetos.css`) **CRIAR**

Usa só **tokens que já existem** no `tokens.css` (`--brand`, `--ink`,
`--surface`, `--line`, `--r-lg`, `--font-mono`, `--font-display`,
`--on-dark`, `--on-dark-soft`, `--dark-line`).

```css
/* ============================================
   PROJETOS — portfólio / casos
   ============================================ */

.projetos-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.projeto {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* card de destaque ocupa a linha inteira e fica lado-a-lado (imagem | texto) */
.projeto.featured {
  grid-column: 1 / -1;
  flex-direction: row;
}
.projeto.featured .projeto-shot { flex: 1 1 50%; }
.projeto.featured .projeto-body { flex: 1 1 50%; }

.projeto-shot {
  background: var(--ink);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
.projeto-shot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.projeto-body {
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.projeto-eyebrow {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--brand);
}
.projeto-body h3 { margin: 0; }
.projeto-tagline { margin: 0; font-size: 18px; font-weight: 600; }

.projeto-ps {
  margin: 0;
  display: grid;
  gap: 4px;
}
.projeto-ps dt {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--brand);
  margin-top: 8px;
}
.projeto-ps dd { margin: 0; line-height: 1.55; }

.projeto-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.projeto-chip {
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 4px 10px;
  border: 1px solid var(--line);
  border-radius: 999px;
}

.projeto-result {
  margin: 0;
  font-weight: 600;
}

.projeto-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 4px;
}
.projeto-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: var(--r-lg);
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.15s ease, background 0.15s ease;
}
.projeto-btn.primary { background: var(--brand); color: #fff; }
.projeto-btn.primary:hover { opacity: 0.9; }
.projeto-btn.ghost { border: 1px solid var(--line); color: inherit; }
.projeto-btn.ghost:hover { background: var(--line); }

/* responsivo */
@media (max-width: 860px) {
  .projetos-grid { grid-template-columns: 1fr; }
  .projeto.featured { flex-direction: column; }
}
```

> Se o seu `tokens.css` usar nomes diferentes (ex.: `--color-brand`), troque nos
> blocos acima. Abra `app/styles/tokens.css` e confira os nomes reais.

**Registrar o CSS** — em `app/globals.css`, na lista de `@import` das seções,
acrescente (perto de `services.css`):

```css
@import "./styles/sections/projetos.css";
```

---

## 7. Passo 6 — Link no menu (`components/layout/Nav.tsx`)

A página `/projetos` é uma rota, não uma âncora. O array `NAV_LINKS` hoje usa
`hash`. Duas opções:

**Opção A (simples) — adicionar âncora `#projetos` à home** *(se você também
colocar a seção na home, Passo 9)*. No `NAV_LINKS`:

```ts
const NAV_LINKS = [
  { hash: '#projetos', label: 'Projetos' },   // ← novo
  { hash: '#servicos', label: 'Serviços' },
  { hash: '#metodo', label: 'Como trabalhamos' },
  { hash: '#sobre', label: 'Sobre' },
  { hash: '#contato', label: 'Contato' },
] as const;
```

**Opção B (rota dedicada) — link direto pra `/projetos`.** Como o `Nav` monta os
links a partir de `hash` (`linkFor`), adicione um link fixo no JSX do menu
(ao lado de onde os `NAV_LINKS` são renderizados):

```tsx
<Link href="/projetos" onClick={() => setMobileOpen(false)}>
  Projetos
</Link>
```

> Recomendo a **Opção B** (rota dedicada) — é o que o plano pede e é melhor pra
> SEO e pra compartilhar o link `reativesystems.com.br/projetos` direto numa
> proposta. Abra o `Nav.tsx`, ache onde os `NAV_LINKS.map(...)` viram `<Link>` e
> coloque o link fixo logo antes/depois.

---

## 8. Passo 7 — Prints/GIFs (`public/projetos/`)

1. Crie a pasta `public/projetos/`.
2. Coloque os arquivos referenciados no content (`studio.png`,
   `content-factory.png`, `churn.png`).
3. Dicas de captura:
   - **Studio**: grave um **GIF curto** (5–8s) do login → dashboard, ou um print
     limpo do dashboard. GIF prova que está vivo.
   - Resolução ~**1600px** de largura, comprima (TinyPNG / `pngquant`) pra não
     pesar. Alvo: < 300 KB por imagem.
   - Mantém proporção parecida entre os cards (ex.: 16:10) pra o grid não pular.
4. Sem print ainda? O card funciona sem `shot` (a imagem some). Mas **com print
   converte muito mais** — priorize pelo menos o do Studio.

> Otimização opcional: trocar `<img>` por `next/image` (`import Image from
> 'next/image'`) pra lazy/resize automáticos. Como o resto do site usa SVG
> inline e não tinha `next/image`, deixei `<img loading="lazy">` pra zero
> config. Migra depois se quiser nota A+ no Lighthouse.

---

## 9. Passo 8 — CTA final (converte!)

O plano é claro: **site sem CTA não converte.** Adicione no fim do
`components/sections/Projetos.tsx` (e exporte; a página do Passo 5 já importa
`ProjetosCta`):

```tsx
import { config, whatsappUrl } from '@/lib/config';
import { Icon } from '@/components/ui/Icon';

export function ProjetosCta(): JSX.Element {
  return (
    <section id="projetos-cta">
      <div className="wrap">
        <div className="projetos-cta-box">
          <h2>Precisa de algo assim pro seu negócio?</h2>
          <p>Me conta o problema — respondo rápido e sem enrolação.</p>
          <div className="projeto-actions">
            <a
              className="projeto-btn primary"
              href={whatsappUrl('Oi! Vi os projetos no site e queria conversar sobre um pra minha empresa.')}
              target="_blank"
              rel="noopener noreferrer"
            >
              Falar no WhatsApp <Icon.ArrowUpRight width={16} height={16} />
            </a>
            <a className="projeto-btn ghost" href={`mailto:${config.contact.email}`}>
              {config.contact.email}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
```

CSS pro box (acrescente em `projetos.css`):

```css
.projetos-cta-box {
  background: var(--ink);
  color: var(--on-dark);
  border-radius: var(--r-lg);
  padding: 48px;
  text-align: center;
}
.projetos-cta-box h2 { margin: 0 0 8px; }
.projetos-cta-box p { margin: 0 0 24px; color: var(--on-dark-soft); }
.projetos-cta-box .projeto-actions { justify-content: center; }
```

> Já existe `whatsappUrl()` e `config.contact.email` no `lib/config.ts` — reuse.
> O número/e-mail saem do environment (ou dos defaults já configurados lá).

---

## 10. Passo 9 (opcional) — Teaser na home

Pra quem cai na home ver que existe portfólio, coloque a seção (ou um recorte)
na home e um botão "ver todos". Em `app/page.tsx`, importe e insira `<Projetos />`
depois de `<Services />` (ou `<TrustStrip />`). Se quiser só um teaser (2 cards +
botão), dá pra criar uma variante depois — por ora, a página dedicada já entrega.

---

## 11. Passo 10 — Rodar, conferir e publicar

```bash
# na raiz do reative-site
npm install            # se ainda não tiver node_modules
npm run dev            # abre http://localhost:3000/projetos
```

**Checklist visual:**
- [ ] `/projetos` carrega, nav e footer aparecem.
- [ ] Card do Studio em destaque (imagem | texto lado a lado no desktop).
- [ ] Botões *Ver ao vivo* abrem `studio...` e *Código* abre o GitHub.
- [ ] **Mobile** (DevTools → 375px): grid vira 1 coluna, destaque empilha.
- [ ] `[[destaques]]` aparecem coloridos (classe `.accent`).
- [ ] Link "Projetos" no menu funciona (desktop e mobile).
- [ ] CTA do WhatsApp abre com a mensagem pré-preenchida.

**Qualidade (antes de subir):**
```bash
npm run lint           # eslint (o repo usa eslint-config-next)
npm run build          # garante que compila pra produção
```

**Publicar (git):**
```bash
git checkout -b feat/pagina-projetos
git add -A
git commit -m "feat(projetos): página /projetos com casos reais + CTA"
git push -u origin feat/pagina-projetos
# abra o PR (ou faça merge na main, conforme seu fluxo)
```

**Deploy:** confira **como o `reative-site` é publicado** (Vercel? VPS?).
- Se for **Vercel**: o push/merge na branch de produção já dispara o deploy.
- Se for **VPS** (como o `studio`): replique o fluxo do prospector
  (`rsync` + script). *Esse repo é separado — confirme antes.*

---

## 12. Checklist final (o que "pronto" significa)

- [ ] `lib/types.ts` com `interface Projeto`.
- [ ] `lib/content/projetos.ts` com 3–4 casos reais (links e slugs do GitHub conferidos).
- [ ] `components/sections/Projetos.tsx` (seção + card) e `ProjetosCta`.
- [ ] `app/projetos/page.tsx` com `metadata` (title, description, canonical, OG).
- [ ] `app/styles/sections/projetos.css` criado **e** importado no `globals.css`.
- [ ] Link "Projetos" no `Nav`.
- [ ] `public/projetos/` com pelo menos o print do Studio.
- [ ] CTA de WhatsApp/e-mail funcionando.
- [ ] `npm run build` passa, mobile ok, links abrem.
- [ ] Deployado e acessível em `https://reativesystems.com.br/projetos`.

---

## 13. Pegadinhas (pra não perder tempo amanhã)

- **Tokens com nome diferente:** se a cor não aparecer, abra `app/styles/tokens.css`
  e ajuste os `var(--…)` deste guia pros nomes reais.
- **Esquecer o `@import`:** criar `projetos.css` sem registrar no `globals.css` =
  página sem estilo. É o erro mais comum.
- **`<Nav external />`:** em páginas que não são a home, sem o `external` os links
  âncora (`#contato`) ficam quebrados. Use `external` na `/projetos`.
- **Repos privados:** não ponha `repoUrl` de repo privado (link 404 quebra a
  confiança). Deixe só *Ver ao vivo*.
- **Imagem pesada:** print de 2 MB derruba o Lighthouse. Comprima.
- **`use client`:** a página e a seção `Projetos` são **server components** (não
  precisam de `'use client'`). Só o `Nav` é client (já tem o diretivo dele).
- **CTA honesto:** a mensagem do WhatsApp já vem pré-escrita — ajuste o texto pro
  seu tom.

---

### Conteúdo de apoio (já decidido no `Plano-Entrar-no-Jogo.md` §2.1)

Ordem de destaque: **1) Reative Studio (Prospector)** — mostrar funcionando é o
trunfo absoluto; **2) Content Factory**; **3) Churn Prediction** (prova visão de
negócio); **4) opcional** Portfólio/Blog. Cada caso:
Problema → Solução → Stack → Resultado, com *Ver ao vivo* + *Código*.
