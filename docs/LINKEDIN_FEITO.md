# 💼 LinkedIn (P5 §6.C) — FEITO

> Log do que já saiu do **agente de LinkedIn** + da **padronização do drawer**.
> Movido do `PLANO-MESTRE.md` §6.C em 2026-06-22 (mesmo padrão de `BLOG_FEITO.md`/
> `FREELA_FEITO.md`). O caminho à frente (Docs-keeper, otimização) segue no plano.

## ✅ EM PRODUÇÃO (2026-06-22)
Deployado no VPS (`studio.reativesystems.com.br`): rsync + `02-deploy.sh` (rebuild
api+web), migrações `b9d3f2a8c1e7` + `c1e8a4d7f3b2` aplicadas (`alembic current` =
head), seed da permissão `linkedin.editar`, health ok.

## Visão / decisões travadas
- **Autônomo no sistema, mas NÃO auto-posta** no LinkedIn (API oficial exige app
  aprovado; auto-post não-oficial arrisca ban). O agente vai sozinho até o
  **rascunho pronto na fila + calendário**; o Pablo revisa, copia/cola e publica.
- **Duas contas** num só modelo via `conta` (`reative` | `pessoal`): Página da
  Reative (institucional) e perfil pessoal do Pablo (1ª pessoa/autoridade) —
  tom diferente no redator.
- *Para no rascunho* + *anti-mentira* (ancorado no Perfil Mestre). Espelha o
  agente de blog (`BLOG_FEITO.md`).

## Fatias (L0–L5, todas testadas c/ Gemini real)
- **L0 — Cano ponta-a-ponta:** modelo `linkedin_post` (conta/formato/hook/body/
  cta/hashtags/status/fonte/scheduled_for…) + migração + repo + service `admin`
  (CRUD + char_count + publicar) + schema + router `/api/linkedin` (perm
  `linkedin.editar`) + registry + tela `LinkedInScreen` **com SidePanel (drawer)**
  (abas por status, filtro por conta, preview "copiar pro LinkedIn", agendamento).
- **L1 — Redator IA:** `analyzers/linkedin/redator` (brief → hook/body/cta/
  hashtags, **sem Markdown**, anti-mentira) com **voz por conta**. `POST /redigir`
  + botão "✍️ Escrever com IA" no drawer.
- **L2 — Coordenador autônomo:** `linkedin_service/coordenador` gera **rascunhos
  prontos** sozinho — `gerar_de_projetos` (cada projeto do Perfil Mestre vira
  case) e `gerar_de_tendencias` (`analyzers/linkedin/temas` propõe N temas →
  redige cada, evita repetir o que já está na fila). `POST /gerar` + "✨ Gerar com IA".
- **L3 — Cross-agent (= B5):** `coordenador.do_blog` plugado em
  `blog_service.admin.mudar_status` (só na 1ª publicação, best-effort/try-except,
  idempotente) → publicar post de blog gera rascunho de divulgação ligado.
- **L4 — Cron + calendário:** `jobs/linkedin_posts.py` (off por default,
  `linkedin_cron_*`) mantém a fila cheia e **agenda `scheduled_for`** espaçado;
  aviso no Telegram. Front: toggle **Lista / 📅 Calendário** (agrupa por dia).
- **L5 — Direção de arte/mídia:** `analyzers/linkedin/midia` (social media pro)
  recomenda a mídia ideal (foto/carrossel/**vídeo-reel**/screenshot/gráfico) com
  **justificativa + roteiro passo a passo + dicas**; campos `midia`/`imagens`
  (migração `c1e8a4d7f3b2`). `POST /midia/sugerir` + `POST /imagem` (gera por IA
  via `image_client` Gemini → MinIO, bucket do blog). Front: seção "🎨 Direção de
  arte" no drawer + **preview fiel do feed do LinkedIn** (toggle Feed/Texto,
  avatar/nome por conta, imagem). Geração de imagem confirmada funcionando.

## Drawer padronizado (S6 — "parecer um sistema só")
`Modal` centralizado → `SidePanel` (drawer estilo Notion) em **15 telas de CRUD**:
CRM (Empresa/Contato/Negócio/Atividade/Projeto), Finanças (Lançamento/Compra/
Cartão/Recorrência + seções Contas/Categorias/Consumo/Orçamentos + Editar
prevista) e o editor do Blog. **Mantidos como `Modal` de propósito** (não são
cadastro): confirmações de pagamento (Pagar/PagarMes/PagarRecorrencia),
`ConfirmarExclusao`, busca global, extrato (leitura). `tsc`/`eslint` verdes.

## Pendências do LinkedIn (continuam no plano)
- Falta reusar InlineCell/Timeline em Vaga e Freela (resto do S6).
- Testar as telas no navegador (validei via smoke de service + tsc/eslint).
