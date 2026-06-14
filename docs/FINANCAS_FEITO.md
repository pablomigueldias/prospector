# O que já está pronto — Agente Financeiro

Registro do que **já foi entregue** no Organizador Financeiro, por categoria
(espelha as seções do `MELHORIAS_FINANCAS.md`, que ficou só com o pendente).
Serve de histórico e de referência de onde cada coisa mora no código.

Última atualização: **2026-06-13**.

> Base do módulo: contas, categorias (árvore), despesas/receitas, cartões/
> parcelas, recorrências, consumo (água/gás/luz), comprovantes (MinIO),
> importador de boleto por IA (Gemini), NLU, bot do Telegram e dashboard
> Next.js ao vivo (SSE) — tudo com smoke tests verdes.

---

## 1b. Bot do Telegram

- ✅ **Comandos base** (2026-06) — `/gasto`, `/ganho`, `/saldo`, `/resumo`, `/help`, `/start` + linguagem natural (card de confirmação) + boleto por foto/PDF. Ref `app/api/services/financas/bot_service.py`.
- ✅ **Cadastrar conta pelo bot** (2026-06-13) — `/contas` lista as contas (nome, tipo, saldo); `/conta <nome> [tipo]` cria (ex.: `/conta Nubank corrente`). O último token vira o **tipo** se for válido (`corrente/dinheiro/vr/va/reserva/cartao_credito`), senão tudo é o nome e o tipo cai pra `corrente`. Tira o atrito de onboarding (não precisa mais do site só pra criar a 1ª conta). Reusa `conta_service.criar_conta`.
- ✅ **Desfazer o último lançamento** (2026-06-13) — `/desfazer` (ou `/undo`) apaga a transação **criada** mais recentemente, revertendo o saldo se estava paga. Backend novo: `transacao_service.ultima_transacao` (ordena por `created_at`). Reusa `excluir_transacao`. Smoke `tests/test_financas_bot_conta_desfazer_api.py`. **Nota de deploy:** se quiser que apareçam no menu do BotFather, republicar `setMyCommands` (o dispatcher já responde de qualquer forma).

## 1. Dashboard web & relatórios

- ✅ **CRUD completo no front** (2026-06-10) — criar/editar/excluir **conta**, **categoria**, **cartão** e **recorrência** por modal, e **lançar/excluir** transação (com reversão de saldo). Tudo sem depender de API/bot.
- ✅ **Lista de transações filtrável** (2026-06-10) — por mês, conta, categoria, tipo e busca na descrição.
- ✅ **Editar transação** (2026-06-11) — botão ✎ por linha abre o form pré-preenchido e salva via `PATCH`, reajustando o saldo (reverte o antigo, aplica o novo). Dividida orienta a excluir/relançar.
- ✅ **Agilidade no dashboard** (2026-06-11) — lançar de qualquer lugar (FAB + atalho `N`/`Ctrl+K`), sub-nav sticky entre seções, lista lembra os últimos filtros (localStorage).
- ✅ **Relatório mensal** (2026-06-11) — seção **Relatório**: série de 3/6/12 meses (receitas × despesas em barras + linha de saldo), totais + despesa média, top categorias e **export CSV**. `GET /api/financas/resumo/relatorio`. Ref `frontend/components/RelatorioSection.tsx`.
- ✅ **Gráficos com Recharts** (2026-06-11) — `recharts@^2` é a lib de gráficos do front (SVG, casa com os tokens `oklch`). Relatório = `ComposedChart` (barras + linha + tooltip custom).
- ✅ **Linha de tendência / variação %** (2026-06-11) — acima do gráfico, compara a despesa do mês mais recente com a média do período (variação %, cor + seta).
- ✅ **Donut "Despesas por categoria" no Recharts** (2026-06-11) — `CategoriaDonut` → `PieChart` (legenda lateral, tooltip com valor + %). Usado no donut do mês e no top categorias do relatório.
- ✅ **Filtrar o relatório por conta/categoria** (2026-06-13) — selects "Conta: todas" / "Categoria: todas" no topo do Relatório recortam a série (ex.: "só Nubank", "só Mercado"). Backend: `GET /resumo/relatorio?conta_id&categoria_id` (conta via EXISTS nos pagamentos, sem fanout em splits). Smoke `tests/test_financas_relatorio_filtro_api.py`. Ref `RelatorioSection.tsx`, `resumo_service.relatorio`, `transacao_repository._filtros_relatorio`.
- ✅ **Exportar o relatório em PDF** (2026-06-13) — botão "Exportar PDF" usa `window.print()` com folha de impressão (`@media print` + classe `print-relatorio`) que isola só a seção Relatório (esconde o resto, some os controles, imprime um cabeçalho com período + recorte). Vira PDF pelo "Salvar como PDF" do navegador. Ref `RelatorioSection.tsx`, `styles/globals.css`.
- ✅ **Clicar no mês do gráfico → lista daquele mês** (2026-06-13) — clicar numa barra/mês do gráfico do Relatório seleciona aquele mês no topo, força a lista de Transações a focar nele (sinal `focarMesSinal`) e rola até lá. Cruza Relatório × Transações. Ref `RelatorioSection.tsx` (onClick do `ComposedChart`), `FinancasScreen.tsx`, `TransacoesSection.tsx`.
- ✅ **Comparar com o ano anterior** (2026-06-13) — toggle "vs {ano-1}" busca a mesma janela um ano antes (reusa o endpoint, sem backend novo) e mostra uma tabela Receitas/Despesas/Saldo/Despesa-média com a variação % (vermelho/verde conforme melhora ou piora). `useRelatorio` ganhou flag `enabled` pra só disparar quando ligado. Ref `RelatorioSection.tsx`.
- ✅ **Busca global de lançamentos** (2026-06-13) — atalho `/` (ou botão "🔍 Buscar" na sub-nav) abre um modal que procura por descrição em **todos os meses**; clicar num resultado leva o dashboard pro mês daquele lançamento. Reusa `GET /transacoes?busca`. Ref `BuscaGlobalModal.tsx`, `FinancasScreen.tsx`.

## 3b. Paridade backend ↔ tela (o que a tela passou a expor)

- ✅ **Importar boleto por foto/PDF pela web** (2026-06-13) — seção **Importar boleto**: arrasta/escolhe um PDF/foto, a IA lê as verbas e cria a despesa **prevista** (ou guarda pra revisão). Categoria opcional. `POST /api/financas/importar/boleto`. Ref `ImportarBoletoSection.tsx`.
- ✅ **Marcar prevista como paga pela tela** (2026-06-13) — botão **✓ Pagar** em toda transação não-paga; modal escolhe a conta quando não tem e move o saldo. `POST /api/financas/transacoes/{id}/pagar`. Fecha o furo do importador.
- ✅ **Processar recorrências manualmente** (2026-06-13) — botão **Gerar previstas** no header de Contas fixas → `POST /api/financas/recorrencias/processar` (gera previstas do mês + marca atrasadas) e recarrega. Conveniência; o cron diário já faz.
- ✅ **Linguagem natural no dashboard** (2026-06-13) — caixa "digite o gasto" acima das Transações: o mesmo NLU do bot (`POST /api/financas/nlu/interpretar`) interpreta o texto, mostra o rascunho (tipo/valor/descrição) com conta e categoria editáveis, e só lança ao confirmar. Ref `NluLancarSection.tsx`.
- ✅ **Despesa dividida (split por N contas)** (2026-06-13) — no form de lançamento (despesa nova), checkbox **Dividir entre contas** abre um editor de pagamentos (conta + valor, add/remover) com checagem soma×total ao vivo; manda `POST /api/financas/transacoes/despesa/dividida`. Ex.: metade VR, metade dinheiro. Ref `TransacoesSection.tsx` (LancamentoForm).
- ✅ **Registrar leitura de consumo pela web** (2026-06-13) — a `ConsumoSection` ganhou **+ Registrar leitura**: modal com tipo (água/gás/luz), mês, leitura atual/anterior e valor opcional (mostra a prévia do consumo). `POST /api/financas/leituras` (já existia, só faltava UI). Ref `ConsumoSection.tsx`.
- ✅ **Despesa auto-split VR/VA na tela** (2026-06-13) — no form de lançamento, ao "Dividir entre contas" há o modo **Auto (esgota o VR)**: escolhe a conta que esgota primeiro e a que cobre o resto; o sistema gasta o saldo do VR/VA e joga o que faltar na 2ª (sempre paga). `POST /api/financas/transacoes/despesa/auto-split` (backend já existia). Ref `TransacoesSection.tsx`.
- ✅ **Ver parcelas de uma compra (visão por compra)** (2026-06-13) — no extrato da fatura, item parcelado ganhou um **ⓘ** que expande **todas as parcelas daquela compra** (nº, vencimento, valor, juros), inclusive as de outros meses. `GET /api/financas/compras/{id}`. Ref `CartoesSection.tsx`.

## 3c. Boletos profissionais

- ✅ **Painel "Contas a pagar"** (2026-06-13) — seção **A pagar** (abas A pagar/Pagas), ordenada por vencimento, vencidos em vermelho + resumo (nº/total/vencidas) e botão ✓ Pagar. Filtro `status` (repetível) + `por_vencimento` no `GET /transacoes`. Ref `ContasAPagarSection.tsx`. **Boleto nunca some:** o importador cria a despesa a pagar mesmo sem separar as verbas (só o total; itens entram quando conferem).
- ✅ **Linha digitável + detector de duplicado** (2026-06-13) — IA extrai a linha digitável (só dígitos, `linha_digitavel`, migration `b2d8f1a3c6e1`); painel A pagar tem "copiar código"; importação não duplica boleto já lançado (chave: linha, ou beneficiário+vencimento+valor). `CopiarLinha.tsx`.
- ✅ **Juros/multa de boleto vencido** (2026-06-13) — IA lê multa % + juros de mora % a.m.; o painel A pagar mostra os vencidos com juros até hoje, e o modal desdobra valor + multa + juros (N dias) = total (recalcula pela data). `encargos.py` / `lib/encargos.ts`. Migration `a1c7e9d2b4f0`. **Multa/juros editáveis no pagamento** (corrige o que a IA leu / cobre boletos antigos; `POST .../pagar` aceita `multa_percentual`/`juros_mensal_percentual`).
- ✅ **Pagar valor diferente do boleto** (2026-06-13) — "Paguei um valor diferente" no modal; o saldo desce pelo valor real e o `valor_total` reflete o que saiu. `POST .../pagar` aceita `valor_pago`.
- ✅ **Editar a conta a pagar do boleto** (2026-06-13) — editor (descrição, valor, vencimento, categoria, multa%/juros% + editor de verbas com soma×total), sem mexer no saldo. `PATCH /transacoes/{id}/conta-a-pagar` → `editar_prevista`. Ref `EditarPrevistaModal.tsx`.
- ✅ **Lembrar categoria/conta por beneficiário** (2026-06-13) — importar sem categoria reaproveita a do último boleto do mesmo beneficiário (`ultima_categoria_por_descricao`); pagar boleto sem conta sugere a **última conta usada** com o beneficiário (`GET /transacoes/{id}/sugestao-conta`).
- ✅ **Desconto por antecipação** (2026-06-13) — IA lê "desconto de R$X até DD/MM"; abate no pagamento se pago até a data.
- ✅ **Importar vários boletos de uma vez** (2026-06-13) — arrasta/seleciona N PDFs/fotos; processa em lote, 1 card por arquivo.
- ✅ **Ver/anexar comprovante no detalhe** (2026-06-13) — o editor da conta a pagar lista os anexos com link e tem "+ anexar". `GET/POST /comprovantes?transacao_id`. ⚠️ Abrir no navegador **só funciona em dev** (MinIO localhost); prod depende do MinIO atrás do Caddy (ver pendência em `MELHORIAS_FINANCAS.md` §6).
- ✅ **Lembrete de vencimento (Telegram)** (2026-06-13) — **APScheduler** no container da API roda 1x/dia (`lembretes_hora`, default 8h, tz America/Sao_Paulo) a `rotina_diaria`: processa recorrências (gera previstas + marca atrasadas) e manda um **digest** com vencidas + vencendo em até N dias (`lembretes_dias_antes`, default 3), com juros/multa. Liga/desliga por `SCHEDULER_ENABLED`/`LEMBRETES_ENABLED`. Teste manual: `POST /api/financas/recorrencias/lembretes/enviar`. Ref `app/jobs/lembretes.py`.
- ✅ **Marcar "atrasada" automático** (2026-06-13) — a `rotina_diaria` roda o `_marcar_atrasadas` todo dia (resolve o cron das recorrências).
- ✅ **Lembrete de fatura de cartão no digest** (2026-06-13) — o digest diário do Telegram ganhou uma seção **💳 Faturas de cartão** com as faturas não pagas que vencem na janela (`lembretes_dias_antes`), com nome do cartão, valor e "vence/venceu DD/MM" + total. Reusa `app/jobs/lembretes.py` (`_faturas_a_vencer`/`_montar_texto_faturas`). Evita pagar fatura com juros. Smoke `test_financas_lembretes` cobre.

## 3d. Cartões profissionais

- ✅ **Lançar compra parcelada/à vista na tela** (2026-06-13) — botão **+ Compra** em cada card de cartão abre um form (descrição, valor total, parcelas, data, categoria, juros opcional); parcelas=1 = à vista. Consome `POST /api/financas/compras`. Ref `CartoesSection.tsx`.
- ✅ **Extrato da fatura** (2026-06-13) — clicar numa fatura abre o detalhe item a item (parcelas/compras, com categoria e juros). `GET /api/financas/cartoes/{id}/faturas/{fatura_id}` → `cartao_service.extrato_fatura`.
- ✅ **Pagar a fatura** (2026-06-13) — botão **Pagar fatura** no extrato: escolhe conta, data e valor opcional; cria uma despesa paga (move o saldo, aparece no resumo do mês) e marca a fatura paga, ligada via `faturas.transacao_id` (migration `d4f0a1b2c3e5`). `POST .../faturas/{fatura_id}/pagar` → `cartao_service.pagar_fatura`. Idempotente (já paga → 400).
- ✅ **Atalho "Pagar fatura" no card do cartão** (2026-06-13) — pedido do Pablo (todo fim de mês quita a fatura via boleto/pix e queria o atalho no próprio card, sem ir ao painel *Contas a pagar* nem abrir a fatura). Botão **Pagar fatura** ao lado do "+ Compra" no card, que abre o fluxo de pagamento **direto no form** (conta/data/valor) apontando pra **fatura mais antiga em aberto** (a que vence agora). Surfacing do `pagar_fatura` que já existe — sem backend novo (prop `iniciarPagando` no `FaturaExtratoModal`). Ref `CartoesSection.tsx`.
- ✅ **Limite e disponível no card** (2026-06-13) — quando o cartão tem `limite`, o card mostra **disponível** = limite − em aberto (vermelho se estourou) + barra de uso (% comprometido, muda de cor a partir de 80%/100%). Front-only (`em aberto` já soma as parcelas futuras). Ref `CartoesSection.tsx`.
- ✅ **Projeção das próximas faturas (básica)** (2026-06-13) — o card lista as próximas faturas em aberto com **mês de competência** + total e link pro extrato. Front-only sobre `/cartoes/{id}/faturas`. (A visão consolidada multi-cartão por mês fica como pendência.)
- ✅ **Projeção consolidada das próximas faturas** (2026-06-13) — bloco "comprometido nos próximos meses" no topo da seção Cartões: soma as faturas **não pagas de todos os cartões** por mês (barrinhas + total), janela de N meses a partir do mês corrente. `GET /api/financas/cartoes/projecao?meses` → `cartao_service.projecao_faturas`. Atualiza sozinho quando um card muda (compra/estorno/pagamento). Smoke `tests/test_financas_projecao_api.py`. Ref `CartoesSection.tsx` (`ProjecaoBlock`).
- ✅ **Estornar compra de cartão** (2026-06-13) — botão ✕ por item no extrato da fatura remove a **compra inteira** (todas as parcelas, deste e dos próximos meses), abate o valor das faturas e some do "em aberto". Bloqueia se alguma parcela já entrou numa fatura **paga** (aí o certo é desfazer o pagamento da fatura antes). `DELETE /api/financas/compras/{id}` → `compra_service.excluir_compra`. Fecha o buraco de "lancei a compra errada e não tinha como apagar". Smoke `tests/test_financas_compra_excluir_api.py`.
- ✅ **Auto-categoria por compra** (2026-06-13) — ao lançar uma compra no cartão, sair do campo de descrição reaproveita a **categoria da última compra com a mesma descrição** (case-insensitive), com a dica "categoria reaproveitada"; trocar na mão limpa o aviso. `GET /api/financas/compras/sugestao-categoria?descricao` → `compra_service.sugerir_categoria`. Espelha o reaproveitamento por beneficiário do boleto. Smoke `tests/test_financas_compra_sugestao_api.py`. Ref `CartoesSection.tsx` (`CompraForm`).
- ✅ **Compra recorrente / assinatura no cartão** (2026-06-13) — recorrência ganhou **forma de pagamento** (conta/cartão/boleto) + cartão alvo (migration `e5a1b3c4d6f7`). Recorrência de cartão vira **compra na fatura** (não prevista de conta): o cron gera sozinho a cada mês (forma-aware) e dá pra **lançar/marcar este mês** na seção Contas fixas (badge de situação + botão). `GET /recorrencias/status`, `POST /recorrencias/{id}/pagar-mes`. E o **boleto importado se liga à conta fixa** (auto pelo beneficiário + select manual no editor da conta a pagar) — resolve "Claude no cartão / aluguel no boleto". Ref `RecorrenciasSection.tsx`, `recorrencia_service.py`, `jobs/recorrencias.py`.

## 3d. Cartões — pagar o mês

- ✅ **Pagar o mês (cartão + boletos juntos)** (2026-06-13) — botão **Pagar o mês** no painel "Contas a pagar" abre um modal com **todas as pendências com vencimento até o fim do mês**: boletos/contas a pagar (com encargos até hoje + conta sugerida) e **faturas de cartão em aberto**. Cada item tem sua conta (editável) e um check; quita tudo de uma vez. `GET /pagar-mes/preview` + `POST /pagar-mes` (orquestra `pagar_transacao` e `pagar_fatura`; falha num item não derruba o lote). Ref `PagarMesModal.tsx`, `pagamento_mes_service.py`. **Importante:** o sistema sempre pagou o mês inteiro de uma vez (a fatura é mensal = soma das parcelas do mês; o "por parcela" é só o extrato). A fatura paga vira uma transação "Fatura {cartão} {mês}" que aparece na lista de **Transações** (histórico mensal).

## 4. Metas, orçamento e alertas

- ✅ **Orçamento por categoria** (2026-06-13) — teto mensal por categoria (tabela `financas.orcamentos`, migration `f6b2c8d4e7a9`). Seção **Orçamentos** no dashboard: barra de progresso consumido×teto (verde→laranja→vermelho a partir de 80%/100%, "estourou" se passar), restante e %, com CRUD por modal. O consumido vem das despesas da categoria no mês (mesma soma do resumo). `GET /orcamentos` + `/orcamentos/status` + POST/PATCH/DELETE. Match por categoria exata (roll-up de subcategoria fica pendente). Ref `OrcamentosSection.tsx`, `orcamento_service.py`.
- ✅ **Alerta de orçamento no Telegram** (2026-06-13) — o digest diário ganhou a seção **📊 Orçamentos no limite**: categorias acima de `ORCAMENTO_ALERTA_PCT`% do teto no mês (🟠 ≥80%, 🔴 ≥100%), com consumido/teto/%. Setting nova `orcamento_alerta_pct` (default 80, exposta no compose/.env.example). `lembretes.py::_texto_orcamento`. Smoke `test_financas_lembretes` cobre (categoria a 112%).

## 6. Confiabilidade & infraestrutura

- ✅ **Cron das recorrências** (2026-06-13) — `rotina_diaria` no APScheduler gera previstas + marca atrasadas todo dia (antes só o endpoint manual). Ver §3c (lembrete de vencimento).
- ✅ **Erro amigável quando falta a `GEMINI_API_KEY`** (2026-06-13) — importar boleto sem a chave agora devolve **400** com mensagem clara ("leitura por IA não configurada, lance manualmente") em vez de **500**, tanto na web quanto no bot (`/gasto` segue). `importador.py::_handle` mapeia `BoletoSemChave`/`GeminiSemChave`. Smoke `tests/test_financas_importar_sem_chave_api.py`.

## 9. Integrações bancárias

- ✅ **PIX copia-e-cola** (2026-06-13) — no form de lançamento, **📋 Colar código PIX** abre uma caixa: cola o BR Code e o sistema extrai **valor + beneficiário** (parser EMV-TLV, sem IA) e preenche descrição/valor. `POST /api/financas/pix/parse` → `pix_service.parse_copia_cola`. Smoke `tests/test_financas_pix_parse_api.py`. Ref `TransacoesSection.tsx`.

---

> Pendências e ideias de evolução: `MELHORIAS_FINANCAS.md`.
> Handoff/operação: `CONTINUACAO.md`.
