# Plano — CRM profissional (uso comercial real)

> Objetivo: transformar o CRM "cru" (hoje só lê Empresas) num CRM **completo,
> usável e profissional** — o que um vendedor/SDR usa de verdade no dia a dia.
> Sub-iniciativa do norte "CRM fora do Notion" (ver `plano-agentes-autonomos.md`
> §1b). Espelha as 5 seções do seu Notion: **Empresas, Contatos, Negócios,
> Atividades, Projetos**.

## O que um profissional comercial exige (e hoje falta)

1. **Ver e editar tudo** — CRUD em todas as entidades, não só leitura.
2. **Filtrar e ordenar** — por status, setor, cidade, dono, valor, data… e
   combinar filtros. (Pedido explícito.)
3. **Pipeline de Negócios** — kanban de *deals* por estágio, com valor e previsão
   (não "empresas por status", que é só organização de contas).
4. **Atividades / follow-ups** — registrar ligação/email/reunião, com vencimento,
   "próxima ação", e ver o que está **atrasado/vencendo hoje**. É o motor diário.
5. **Ficha 360 da empresa** — uma tela que junta contatos + negócios + atividades
   + notas + **linha do tempo** do que os agentes fizeram.
6. **Dashboard comercial** — valor no pipeline, conversão, atividades do dia,
   ganhos no mês.

---

## Arquitetura (encaixa no padrão do projeto)

- **Backend:** fatias verticais (`schemas/crm.py`, `services/crm_service.py`,
  `routers/crm.py`, repos). Modelos novos em `db/models/` + migração Alembic.
- **Frontend:** `components/crm/` — um **shell** com navegação das 5 seções; cada
  seção tem tabela + filtros + CRUD; ficha 360 em modal/rota.
- **Filtros:** uma barra reutilizável (`CrmFiltros`) que monta querystring; o
  backend filtra no Postgres (índices já existem pra estado/cidade/setor/score).
- **Escrita:** Postgres é a fonte. Durante a transição, **dual-write** opcional
  reflete a edição no Notion (Slice I). Depois desliga.
- **Memória/timeline:** toda ação de CRUD/agente vira `pipeline_event`
  (`agente`/`alvo_tipo`/`alvo_id`) — a convergência com o MAS.

---

## Roadmap por fatias (cada uma = 1 commit testável)

### Slice A — Shell das 5 seções ⏳
Navegação **Empresas · Contatos · Negócios · Atividades · Projetos** dentro do
agente CRM. Empresas/Contatos ativas; as 3 novas como "em breve" até serem
espelhadas do Notion.

### Slice B — Empresas: CRUD + filtros + ordenação
**Backend ✅ FEITO (2026-06-17):** `POST/PUT/DELETE /api/crm/empresas`,
filtros em `GET /empresas` (status, setor, estado, cidade, tamanho, score_min,
como_conheceu, busca) + `ordenar_por`/`desc` + `GET /empresas/facetas` (valores
distintos pros dropdowns). Repo: `_filtro/_ordenacao/excluir/facetas`. Verificado
HTTP+in-process (criar/editar/excluir, filtro setor=18, estado SP=33). Corrigido
bug NOT NULL: `status`/`como_conheceu` só sobrescrevem quando vêm preenchidos.
**Frontend ✅ FEITO (2026-06-17):** `CrmScreen` virou shell com navegação das 5
seções (Empresas/Contatos ativas; Negócios/Atividades/Projetos "em breve").
`EmpresasSection` = barra de filtros (busca + status/setor/estado/tamanho via
dropdowns das facetas) + toggle Tabela/Kanban + "Nova empresa" + form de
criar/editar (modal) + excluir com confirmação + detalhe com botão Editar.

### Slice C — Contatos: lista + CRUD + filtros
**Backend ✅ FEITO (2026-06-17):** `GET/POST/PUT/DELETE /api/crm/contatos`
(lista com nome da empresa, filtros: busca/empresa_id/decisor/origem). Repo
`ContatoRepository.listar/contar/excluir`.
**Frontend ✅ FEITO (2026-06-17):** `ContatosSection` = tabela + filtros (busca,
empresa, decisor) + "Novo contato" + form (modal, com select de empresa) +
excluir com confirmação. Tudo verificado: tsc+lint verdes, /agents/crm 200.

### Slice D — Negócios (pipeline de vendas) — espelhado do Notion
**Dados + leitura ✅ FEITO (2026-06-17):** descobri as 5 bases do Notion via
`search`, adicionei os IDs no config, criei modelo `negocios` (estágio, valor,
probabilidade, origem, tipo_servico, previsão, próxima ação, FK empresa+contato),
migração `e2f5b8c1d934`, e estendi o importador (relações amarradas via
notion_page_id). API: `GET /negocios`, `GET /negocios/pipeline` (agrupa por
estágio + **forecast ponderado** Σ valor×prob). Front: `NegociosSection` (pipeline
por estágio + StatCards de valor/forecast). Verificado: forecast R$262,50 (350×75%).
**CRUD ✅ FEITO (2026-06-17):** `POST/PUT/DELETE /negocios` + `NegocioForm`
(selects de empresa+contato, tipo_servico, datas) + card clicável/excluir.
**Pendente:** drag entre estágios.

### Slice E — Atividades (motor diário) — espelhado do Notion
**Dados + leitura ✅ FEITO (2026-06-17):** modelo `atividades` (tipo, status,
data, resumo, próximos passos, FK negócio+contato), importado. API
`GET /atividades`. Front: `AtividadesSection` (tabela). **CRUD ✅ FEITO:**
`POST/PUT/DELETE /atividades` + `AtividadeForm` (selects negócio+contato,
datetime). **Pendente:** visões "hoje/atrasadas/próximas" + lembretes via `jobs/`.

### Slice F — Projetos — espelhado do Notion
**Dados + leitura ✅ FEITO (2026-06-17):** modelo `projetos` (classe `ProjetoCRM`
pra não colidir com o Projeto do freela; status, valor total/recebido, a receber
calculado, prazos, links, FK empresa+negócio origem), importado. API
`GET /projetos`. Front: `ProjetosSection` (tabela com financeiro). **CRUD ✅
FEITO:** `POST/PUT/DELETE /projetos` + `ProjetoForm` (selects empresa+negócio,
valores, datas, links). ✅ **Empresas, Contatos, Negócios, Atividades e Projetos
agora têm CRUD completo no sistema — paridade de dados com o Notion.**

### Slice G — Ficha 360 da empresa ✅ FEITO (2026-06-17)
O detalhe da empresa (modal) puxa `GET /empresas/{id}/relacionados` e mostra
**Negócios + Projetos + Atividades** ligados, além de contatos/sócios/notas. O
raio-x do cliente numa tela só.

### Slice H — Dashboard comercial ✅ FEITO (2026-06-17)
Aba **"Visão geral"** (default) com `GET /crm/dashboard`: valor no pipeline,
**forecast ponderado**, negócios abertos, barra por estágio, atividades
pendentes/atrasadas, projetos a receber, clientes ativos. StatCards + barras.

### Slice I — Sync Notion ✅ (pull) / Dual-write ❌ (não feito de propósito)
Botão **"↻ Sincronizar do Notion"** no header do CRM (`POST /crm/sincronizar-notion`
→ re-importa as 5 bases, idempotente). **Push de volta pro Notion (dual-write na
edição) foi deixado de fora de propósito:** o objetivo é SAIR do Notion, então
escrever de volta seria contraproducente e arriscado.

### Extras ✅ FEITO (2026-06-17)
- **Drag no pipeline:** arrastar card de negócio entre estágios
  (`PATCH /negocios/{id}/estagio`, não clobbera os outros campos).
- **Atividades — views hoje/atrasadas:** filtro Todas/Pendentes/Atrasadas +
  destaque vermelho nas atrasadas (data passada e não concluída).

---

## Recursos transversais
- ✅ **Filtros + busca + ordenação** (Empresas/Contatos/Atividades).
- ✅ **Sync do Notion** por botão (idempotente).
- ⏳ **Export CSV** (backlog leve — o import do Notion já existe).
- **Permissões:** CRM é Reative (aberto a logado), como o Prospector.

---

## 🔧 Ajustes pedidos (2026-06-18, via prints do Notion)

### Parte A — Selects canônicos ✅ FEITO
Vários campos estavam como texto livre; viraram **dropdowns com as opções exatas
do Notion** (constantes em `config.py`, expostas via `GET /api/crm/opcoes`,
consumidas pelos forms). Catálogo:
- **Empresa:** Setor, Tamanho, Status, Como conheceu, Estado (já existiam no config).
- **Negócio:** Estágio (⚪ Lead novo · 🔵 Primeiro contato · 🟣 Qualificado · 🟡 Briefing
  agendado · 🟠 Briefing realizado · 🔴 Proposta enviada · 🔴 Em negociação · 🟢 Ganho ·
  ⚪ Perdido · 🟣 Standby), Probabilidade (10/25/50/75/90%), Origem, Tipo de serviço
  (multi: Landing page/Site institucional/Sistema web/Automação/Bot/Manutenção/Consultoria).
- **Atividade:** Status (🟡 Agendada · 🟢 Realizada · 🔴 Não compareceu · ⚪ Cancelada),
  Tipo (📞 Call · 💬 WhatsApp · ✉️ E-mail · 🤝 Reunião presencial · 💼 LinkedIn DM · 🎥 Videocall).
- **Projeto:** Status (🆕 Onboarding · 🛠️ Em desenvolvimento · 🚀 Em produção · 👀 Em
  revisão · ⏸️ Pausado · ✅ Concluído), Tipo de serviço, Forma de pagamento (À vista/50-50/
  40-30-30/Mensal/Outro).
- A **ordem do pipeline** e do **kanban de status** passou a usar esses estágios reais.

### Parte B — Navegação relacional bidirecional ✅ FEITO (2026-06-18)
No Notion, clicar numa empresa mostra contatos/negócios/projetos **clicáveis**; do
contato volta pra empresa; do negócio vai pro projeto; tudo interligado nos 2 sentidos.
Implementado:
1. **Backend — record universal:** `GET /crm/record/{tipo}/{id}` (empresa|contato|
   negocio|projeto|atividade) devolve `{titulo, campos, grupos[{titulo, itens[link]}],
   notas}` — cada link é `{tipo, id, nome, sub}` navegável. `selectinload(Contato.empresa)`
   p/ evitar lazy-load fora do contexto async.
2. **Frontend — `RecordModal` com pilha de navegação:** modal único que recebe
   `{tipo, id}`, renderiza campos + **chips clicáveis das relações**; clicar empilha o
   próximo registro (botão "← voltar"). Editar só no topo da pilha.
3. Seções Negócios/Atividades/Projetos abrem o RecordModal ao clicar (com Editar →
   form). A ficha 360 da empresa virou **relacionados clicáveis** (contato/negócio/
   projeto/atividade abrem o RecordModal empilhado), preservando sócios/links sociais.
Verificado: empresa→contato→empresa (bidirecional), negócio→{empresa,contato,projetos,
atividades}, projeto→{empresa,negócio}, atividade→{negócio,contato}. tsc+lint+ruff verdes.

---

## 🚀 Saída do Notion — sistema dinâmico e de manuseio direto (2026-06-18)

> Decisão do Pablo: **parar de usar o Notion**; o sistema é a fonte única, tudo
> editável direto, dinâmico e intuitivo. Quatro frentes, todas FEITAS:

1. **Edição inline nas tabelas ✅** — `PATCH /crm/record/{tipo}/{id}` (campos
   parciais, allowlist + coerção por tipo no `crm_service`). Front: `InlineCell`
   (click-to-edit texto/número/data/select/bool) nas tabelas de Empresas,
   Contatos, Atividades, Projetos e nos cards de Negócios. Salva ao sair; Esc
   cancela.
2. **Editar dentro da navegação ✅** — `record_detalhe` agora emite metadados por
   campo (`campo/kind/opcoes_key/raw`); o `RecordModal` renderiza `InlineCell` em
   qualquer registro navegado (não só na origem) + **"+ novo" relacionado** com a
   FK pré-preenchida (forms ganharam prop `inicial`).
3. **Opções gerenciáveis ✅** — tabela `crm_opcoes` (grupo/valor/cor/ordem/ativo),
   migração `a3d8f1c47e90` com seed das opções atuais (cor derivada do emoji).
   `GET /crm/opcoes` lê do banco; kanban/pipeline/dashboard ordenam pela ordem do
   banco. CRUD em `/crm/opcoes/*` (criar/listar/editar/excluir/reordenar; renomear
   propaga aos registros que usam o valor). UI: `OpcoesManager` (painel ⚙ Opções
   no header) com cor, ordem (↑↓), ativar/desativar e add por grupo.
4. **Aposentar o Notion na UI ✅** — removido o botão "↻ Sincronizar do Notion" do
   header (a rota/importer continuam no repo, só saíram da tela).

**UX — painel lateral (drawer):** a ficha do registro deixou de ser um modal
central apertado e virou um **SidePanel deslizante da direita** (estilo Notion,
`components/shared/SidePanel.tsx`), usado pelo `RecordModal`, pela ficha 360 da
empresa e pelo Contato (que antes abria o form direto). Campos em layout
rótulo|valor.

**Refinos (2026-06-18, 2º lote):**
- **Drawer em todas as seções:** Contatos agora abre o `RecordModal` (Editar →
  form), igual a negócios/atividades/projetos.
- **Pílulas coloridas:** `GET /crm/opcoes/cores` (grupo→valor→cor); `InlineCell`
  pinta o select pela cor (helper `pilulaCor` em `_crmShared`); aplicado em
  Empresas/Atividades/Projetos/Negócios e no `RecordModal`.
- **Lista ⇄ Kanban:** componentes reutilizáveis `VistaToggle` + `KanbanGenerico`
  (drag entre colunas → `PATCH record {status}`). Negócios ganhou **Lista** (além
  do pipeline); Atividades e Projetos ganharam **Kanban** por status.

---

## ✅ STATUS: plano essencialmente COMPLETO (2026-06-17)
As 5 seções do Notion (Empresas, Contatos, Negócios, Atividades, Projetos) vivem
no sistema com **CRUD completo, filtros, pipeline com forecast, ficha 360,
dashboard, drag e sync do Notion**. Backlog leve restante: export CSV, gráficos
Recharts no dashboard, lembretes de atividade via `jobs/`, e (se um dia quiser)
dual-write pro Notion.

---

## Ordem sugerida
A → **B (em andamento)** → C → G (ficha 360, dá o "sentir profissional") → D
(pipeline) → E (atividades) → H (dashboard) → F → I.

> As 3 seções novas (D/E/F) dependem de você **compartilhar as bases do Notion**
> (Negócios, Atividades, Projetos) — aí eu espelho estrutura + dados, igual fiz
> com Empresas/Contatos.
