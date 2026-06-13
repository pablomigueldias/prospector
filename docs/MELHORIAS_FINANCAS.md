# Melhorias possíveis — Agente Financeiro

Backlog de evolução do Organizador Financeiro. Não é obrigação — é um cardápio
de ideias, com **prioridade sugerida** (🔴 alta / 🟡 média / 🟢 baixa) e o
*porquê*. O módulo hoje já cobre o essencial (contas, categorias, despesas/
receitas, cartões/parcelas, recorrências, consumo, comprovantes, importador de
boleto por IA, NLU, bot e dashboard ao vivo) e agora também o **CRUD completo
pela web** (conta, categoria, transação, recorrência e cartão — criar/editar/
excluir sem depender de API/bot). O que falta é, sobretudo, **fechar o loop de
gestão** (orçar, alertar, relatar), **deixar de ser registrador e virar
copiloto** (§8–§10) e polir as bordas.

Última revisão: 2026-06-13.

---

## 1. Bot do Telegram (onde você mais usa)

- 🔴 **Cadastrar conta pelo bot** — `/conta Nubank corrente` e `/contas` pra listar. Hoje precisa do site só pra criar a 1ª conta; é o maior atrito de onboarding.
- 🔴 **Editar/excluir o último lançamento** — `/desfazer` ou um botão "↩️ Desfazer" no card de confirmação. Erro de digitação acontece direto.
- 🟡 **Lançar despesa prevista / agendada** — *"vou pagar 200 de luz dia 10"* → cria como `prevista`. Hoje o bot só lança como `paga`.
- 🟡 **Resumo por período** — `/resumo julho`, `/resumo semana`, e "quanto gastei em mercado esse mês?".
- 🟡 **Confirmação mais rica** — no card, deixar trocar a **categoria** e a **conta** por botões (hoje só Confirmar/Cancelar/Editar).
- 🟢 **Lembrete proativo** — mensagem no Telegram quando uma conta fixa está pra vencer ou ficou atrasada (depende de §4).
- 🟢 **Atalhos de conta** — apelidos (`vr`, `nu`) configuráveis por usuário em vez de casar pelo nome/tipo.

## 2. Casal / multi-usuário

- 🟡 **Atribuição por pessoa (mantendo a carteira junta)** — gravar *quem* lançou (Pablo/Monique) mesmo caindo na mesma carteira, pra depois ver "quem gastou o quê". Hoje os dois viram o mesmo `usuario_id` e some essa informação.
- 🟡 **Renomear o "slot 2"** — as vars `TELEGRAM_*_SANDRA` são legado; trocar por algo neutro (`_2`) ou, melhor, um **mapa chat→usuário em tabela** (suporta N pessoas sem mexer no `.env`).
- 🟢 **Visão "individual vs casal"** — alternar no dashboard entre o consolidado e o de cada pessoa (depende da atribuição acima).

## 3. Dashboard web & relatórios

- ✅ **CRUD completo no front** (2026-06-10) — criar/editar/excluir **conta**, **categoria**, **cartão** e **recorrência** (contas fixas) por modal, e **lançar despesa/receita** + **excluir** transação (com reversão de saldo) pela interface. Tudo gerenciável sem depender de API/bot.
- ✅ **Lista de transações filtrável** (2026-06-10) — por mês, conta, categoria, tipo e busca na descrição.
- ✅ **Editar transação** (2026-06-11) — botão ✎ em cada linha abre o formulário pré-preenchido e salva via `PATCH`, reajustando o saldo da conta (reverte o efeito antigo e aplica o novo). Vale pra transação de uma conta; dividida orienta a excluir e relançar.
- ✅ **Agilidade no dashboard** (2026-06-11) — lançar de qualquer lugar (FAB flutuante + atalho `N`/`Ctrl+K`), sub-nav sticky pra pular entre seções, e a lista lembra os últimos filtros (localStorage).
- ✅ **Relatório mensal** (2026-06-11) — seção **Relatório**: série de 3/6/12 meses com receitas × despesas (barras) + **linha de saldo**, totais do período + despesa média, top categorias do período e **export CSV**. Endpoint `GET /api/financas/resumo/relatorio`.
- ✅ **Gráficos com Recharts** (2026-06-11) — adotada a **Recharts** (`recharts@^2`) como lib de gráficos do front (padrão de mercado em React, SVG, casa com os tokens `oklch` do design — vs. Tremor, que traz preset Tailwind próprio e conflita). O 1º remendo do relatório foi feito à mão e não renderizava as barras; agora é `ComposedChart` (barras + linha + tooltip custom). Ref: `frontend/components/RelatorioSection.tsx`. *Próximo gráfico novo: pintar com as cores oklch direto nas props.*
- 🟢 **Detalhe de cartão** — extrato da fatura, parcelas futuras, projeção de quanto vai pesar nos próximos meses.
- 🟢 **Atalhos & produtividade (resto)** — falta busca global e dark mode (atalho de teclado e lembrar filtros já feitos).

### Novas recomendações (2026-06-11) — evoluir Dashboard & relatórios
- 🟡 **Export PDF do relatório** — o CSV já saiu; falta um PDF "bonito" (cabeçalho, gráfico, totais) pra mandar/arquivar. Dá pra renderizar no front (ex.: `window.print()` com uma folha de estilo de impressão) ou gerar no backend.
- 🟡 **Filtrar o relatório por conta/categoria** — hoje a série é do consolidado; poder recortar "só Nubank" ou "só Mercado" ao longo dos meses ajuda a achar onde o gasto cresce.
- ✅ **Linha de tendência / variação %** (2026-06-11) — acima do gráfico, compara a despesa do mês mais recente com a média do período e mostra a variação % (acima/abaixo, com cor e seta). Falta o recorte por mês anterior e por categoria.
- 🟢 **Evolução de saldo real (patrimônio no tempo)** — hoje "saldo por mês" é o *resultado* (receitas − despesas) do mês; o saldo acumulado das contas ao longo do tempo exige snapshots (não guardamos histórico). Encaixa com o §10 (patrimônio líquido).
- 🟢 **Clicar no mês do gráfico → abre a lista filtrada** daquele mês (cruza o Relatório com a seção Transações).
- 🟢 **Comparar dois períodos** lado a lado (este mês vs. mesmo mês do ano passado).
- ✅ **Donut "Despesas por categoria" no Recharts** (2026-06-11) — `CategoriaDonut` virou `PieChart` da Recharts (mesma interface, legenda lateral mantida, tooltip no hover com valor + %). Usado no donut do mês e no top categorias do relatório.

## 3b. Paridade backend ↔ tela (o backend já faz, a tela ainda não)

> Levantamento 2026-06-11 cruzando os routers de `financas` com o `lib/api.ts`/
> componentes. **Objetivo: poder fazer TUDO pela tela de Finanças** (e, quando
> fora de casa, pelo bot — que já cobre NLU, boleto por foto e lançamento).
> Estas funções **já existem no backend**, só falta a interface no front.

- ✅ **Importar boleto por foto/PDF pela web** (2026-06-13) — seção **Importar boleto** no dashboard: arraste (ou escolha) um PDF/foto, a IA lê as verbas e, se batem com o total, já cria a despesa **prevista**; senão guarda pra revisão manual. Categoria opcional. `POST /api/financas/importar/boleto`. Ref `frontend/components/ImportarBoletoSection.tsx`. Replica o "boleto por foto" do bot no desktop — era o item de maior valor da §3b.
- ✅ **Juros/multa de boleto vencido** (2026-06-13) — a IA lê os encargos do boleto (multa % + juros de mora % a.m.); o painel A pagar mostra os vencidos já com os juros acumulados até hoje, e o modal de pagamento desdobra valor + multa + juros (N dias) = total (recalcula pela data). Ao pagar, o saldo desce pelo total e o que foi de encargos fica em `encargos_pagos`. `encargos.py` (back) / `lib/encargos.ts` (front). Migration `a1c7e9d2b4f0`. **Multa/juros editáveis no modal de pagamento** — corrige o que a IA leu errado e cobre **boletos antigos** (importados antes da feature, sem os percentuais); o valor digitado recalcula o total e fica salvo (`POST .../pagar` aceita `multa_percentual`/`juros_mensal_percentual`).
- ✅ **Painel "Contas a pagar"** (2026-06-13) — seção **A pagar** com abas *A pagar* / *Pagas*, ordenada por vencimento, **vencidos em vermelho** + resumo (nº/total/vencidas) e botão ✓ Pagar. Filtro `status` (repetível) + `por_vencimento` no `GET /transacoes`; `data_vencimento` na lista. Ref `frontend/components/ContasAPagarSection.tsx`. **Boleto nunca some:** o importador agora cria a despesa a pagar mesmo quando não consegue separar as verbas (só o total; itens entram quando conferem) — antes ia pra "revisão manual" e não criava nada.
- ✅ **Marcar prevista como paga pela tela** (2026-06-13) — botão **✓ Pagar** em toda transação não-paga (boleto importado, recorrência ou prevista do form). Modal escolhe a conta quando a transação ainda não tem (boleto/recorrência nascem sem) e move o saldo ao confirmar. `POST /api/financas/transacoes/{id}/pagar`. **Fecha o furo do importador**: antes o boleto virava prevista e não havia como quitar/controlar pela web. Ref `frontend/components/TransacoesSection.tsx` (PagarModal).
- 🟡 **Compra parcelada no cartão** — `POST /api/financas/compras` (`CompraParceladaCreate`): lançar "geladeira em 10x no cartão" e o sistema gera as parcelas/faturas. Não existe na tela — hoje só dá pra cadastrar o cartão, não comprar nele.
- 🟡 **Boleto parcelado** — `POST /api/financas/compras/boleto` (`BoletoParceladoCreate`): boleto que vira N parcelas. Ausente no front.
- 🟡 **Despesa dividida (split por N contas)** — `POST /api/financas/transacoes/despesa/dividida`: pagar uma despesa com mais de uma conta (ex.: metade VR, metade dinheiro). O form de lançamento só faz conta única. *(É também o que destrava editar transações divididas — ver §3 "Editar transação".)*
- 🟡 **Despesa auto-split VR/VA** — `POST /api/financas/transacoes/despesa/auto-split`: esgota o VR e joga o resto no dinheiro automaticamente. Resolve "às vezes acaba o VR" — só existe no backend.
- 🟡 **Registrar leitura de consumo pela web** — `POST /api/financas/leituras`: a `ConsumoSection` só **lê** (GET); não dá pra lançar a leitura de água/gás/luz manualmente na tela (hoje só chega via boleto de condomínio).
- 🟢 **Anexar comprovante pela web** — `POST /api/financas/comprovantes`: a galeria só **lista** (GET); anexar um comprovante a uma transação é só pelo bot. Falta o upload na tela. *(Depende também de expor o MinIO atrás do Caddy — §6 — pra a imagem abrir no browser.)*
- 🟢 **Linguagem natural no dashboard** — `POST /api/financas/nlu/interpretar`: uma caixa "digite o gasto" na tela (ex.: *"gastei 30 no mercado"*) usando o mesmo NLU do bot, caindo no card de confirmação. Casa com o §8 (perguntas/assistente).
- 🟢 **Processar recorrências manualmente** — `POST /api/financas/recorrencias/processar`: um botão "gerar previstas / marcar atrasadas" na seção Contas fixas (enquanto o cron do §6 não existe).
- 🟢 **Detalhe de compra parcelada** — `GET /api/financas/compras/{id}`: ver as parcelas de uma compra específica (depende de existir o lançamento de compra parcelada acima).

> Já cobertos na tela (pra referência): CRUD de conta/categoria/cartão/recorrência,
> lançar despesa/receita simples, editar/excluir transação, lista filtrável,
> resumo, relatório, faturas do cartão e a galeria de comprovantes (leitura).

## 3c. Boletos profissionais (carro-chefe — Pablo vai alimentar muito)
Meta declarada (2026-06-13): deixar o boleto "bem profissional e super útil".
Ordem de ataque por custo/benefício (evitar as dores mais caras primeiro):

- ✅ **Linha digitável + detector de duplicado** (2026-06-13) — IA extrai a linha digitável (só dígitos, `linha_digitavel`, migration `b2d8f1a3c6e1`); painel A pagar tem "copiar código"; importação não duplica boleto já lançado (chave: linha digitável, ou beneficiário+vencimento+valor). `CopiarLinha.tsx`.
- 🔴 **Lembrete de vencimento (Telegram)** — avisar X dias antes / no dia / vencido. Depende de **cron diário** (job `/recorrencias/processar` já existe, falta agendar). Evita pagar com juros por esquecimento.
- 🟡 **Marcar "atrasada" automático** — hoje o status fica "prevista" mesmo vencido (a tela só pinta de vermelho client-side); o cron acima corrige o status no banco.
- ✅ **Editar a conta a pagar do boleto** (2026-06-13) — botão ✎ nas contas a pagar abre um editor (descrição, valor, vencimento, categoria, multa%, juros% e **editor de verbas** com add/remover + checagem soma×total). Não mexe no saldo (não foi paga). `PATCH /transacoes/{id}/conta-a-pagar` → `editar_prevista`. Ref `frontend/components/EditarPrevistaModal.tsx`. Resolve o "a IA não separou bem".
- 🟡 **Pagar valor diferente do boleto** — ajustar o valor final pago (acordo/desconto manual) pra o saldo bater com o que saiu de verdade.
- 🟡 **Lembrar categoria/conta por beneficiário** — reimportou "Condomínio Lello" → sugere a categoria e conta da última vez.
- 🟡 **Virar conta fixa (recorrência)** — detectar boleto que se repete e oferecer transformar em recorrência.
- 🟡 **Ver boleto/recibo no painel + anexar comprovante de pagamento** — depende de **expor o MinIO atrás do Caddy** (§6).
- 🟢 **Passo de revisão antes de criar**, **sanity checks** (valor 0 / data improvável / soma≠total), **desconto por antecipação** (IA ler "desconto até dia X"), **importar vários boletos de uma vez**, **histórico do boleto** (original × pago × encargos).

## 4. Metas, orçamento e alertas (o "loop de gestão")

- 🔴 **Orçamento por categoria** — definir um teto mensal (ex.: R$ 800 em mercado) e o sistema acompanhar o consumido x previsto. *Ficou de fora no build original (sem tabela de metas).*
- 🟡 **Alertas** — avisar (no Telegram) quando estourar X% de uma categoria, quando uma conta fixa vencer/atrasar, ou quando o saldo previsto do mês ficar negativo.
- 🟡 **Projeção de fim de mês** — com base nas recorrências previstas + média, dizer "sobra estimada: R$ Y".
- 🟢 **Reservas com objetivo** — meta de valor numa conta tipo reserva (ex.: "viagem: R$ 5.000") com barra de progresso.

## 5. Importador / IA

- 🟡 **Importar extrato bancário (OFX/CSV/PDF)** — conciliar muitos lançamentos de uma vez, não só boleto a boleto.
- 🟡 **Categorização automática** — sugerir a categoria pela descrição (aprende com o histórico), reduzindo o "Editar" no card.
- 🟢 **Ler comprovante PIX / nota fiscal** — estender o importador além de boleto.
- 🟢 **Detectar duplicado** — avisar quando um boleto/PIX parece já ter sido lançado.

## 6. Confiabilidade & infraestrutura

- 🔴 **Expor o MinIO atrás do Caddy** — pra as imagens de comprovante **abrirem no navegador** (hoje a URL presignada aponta pro `minio:9000`, inacessível ao browser). Inclui ajustar `S3_ENDPOINT` público + `img-src` do CSP.
- 🟡 **Job das recorrências automático** — hoje `/recorrencias/processar` existe mas não há cron chamando. Agendar (cron no VPS ou scheduler interno) pra gerar previstas e marcar atrasadas todo dia.
- 🟡 **Monitoramento/alerta de saúde** — ping no `/api/health` + aviso se a API cair; checar o cron de backup.
- 🟢 **Testar o restore do backup** — restaurar um dump num banco de teste e confirmar que volta inteiro.
- 🟢 **Observabilidade** — logs estruturados + métricas (quantos lançamentos/dia, latência do importador).
- 🟡 **Testes E2E / verificação visual (Playwright)** — hoje a validação de tela é manual (a API/lógica têm smoke tests, mas o front não). Um Playwright que faz login automatizado e tira screenshot/roda smoke das telas (Finanças, lançar, editar) dá pra conferir mudanças de UI sem subir e clicar à mão. *Surgiu em 2026-06-11 quando não deu pra screenshotar a tela autenticada sem browser automatizado.*

## 7. Segurança & dados

- 🟡 **2FA obrigatório pro admin** — hoje é opcional; tornar exigido pra quem tem `usuarios.gerenciar`.
- 🟢 **Exportar meus dados** — botão "baixar tudo" (LGPD-friendly), CSV/JSON de transações.
- 🟢 **Trilha de auditoria no front** — visualizar os eventos de segurança (login, troca de senha, 2FA) numa tela.

## 8. Inteligência do agente (de registrador a copiloto)

O módulo registra bem; o salto é ele **entender e antecipar**. Tudo aqui é
território de IA (Gemini/Groq, que já estão no stack) + as consultas que já existem.

- 🔴 **Perguntas em linguagem natural sobre os dados** — *"quanto gastei com mercado nos últimos 3 meses?"*, *"qual meu maior gasto de junho?"*, *"dá pra parcelar isso?"*. Um agente com *tool calling* sobre os endpoints de resumo/transações responde sem o usuário virar relatório. Vale no dashboard e no bot.
- 🔴 **Categorização automática que aprende** — sugerir a categoria pela descrição usando o histórico do próprio usuário (e confirmar com 1 toque). Reduz drasticamente o atrito de lançar. (Hoje o §5 cita; aqui é prioridade.)
- 🟡 **Insights proativos (digest)** — resumo semanal/mensal automático no Telegram: "essa semana você gastou R$ X (−12% vs. média), top categoria: delivery". Transforma o bot em assistente, não só caixa de entrada.
- 🟡 **Detector de assinaturas/recorrências não cadastradas** — achar cobranças que se repetem ("parece que você paga Spotify todo mês — quer cadastrar como conta fixa?") e oferecer virar recorrência.
- 🟡 **Alerta de anomalia** — gasto muito fora do padrão da categoria/mês dispara um aviso ("R$ 800 em farmácia, 4x sua média").
- 🟢 **Áudio no bot** — mandar um áudio ("gastei trinta no uber") → transcrição (Whisper/Groq) → NLU → card. Mais rápido que digitar.
- 🟢 **Coach de metas** — quando houver orçamento (§4), o agente comenta o ritmo ("no dia 10 você já usou 60% do teto de mercado").

## 9. Integrações bancárias (matar o lançamento manual)

O maior atrito é digitar cada gasto. Puxar do banco resolve isso de vez.

- 🔴 **Open Finance (Pluggy/Belvo)** — conectar a conta/cartão e importar transações automaticamente, com conciliação contra o que já foi lançado. É o "santo graal" do organizador.
- 🟡 **Importar fatura de cartão (PDF/CSV)** — ler a fatura inteira e gerar as compras/parcelas de uma vez, conciliando com a fatura já existente.
- 🟡 **Ler comprovante de PIX / nota fiscal** — estender o importador de boleto pra PIX e NF (QR/imagem) — já citado no §5, encaixa aqui.
- 🟢 **Pix copia-e-cola** — colar o código PIX e o agente extrai valor/beneficiário e pré-preenche o lançamento.

## 10. Patrimônio e planejamento (além do fluxo de caixa)

- 🟡 **Patrimônio líquido** — somar contas + reservas − dívidas (faturas/parcelas em aberto) e acompanhar a evolução mês a mês. Sai do "quanto entrou/saiu" pro "quanto eu tenho".
- 🟢 **Investimentos** — registrar aportes/saldo de investimentos (mesmo manual) pra ter a foto completa, não só o dia a dia.
- 🟢 **Relatório anual / IRPF** — consolidado do ano por categoria, exportável, pensando no imposto de renda.
- 🟢 **Multi-perfil/visão** — quando a atribuição por pessoa (§2) existir, alternar entre "casal" e "Pablo/Monique" nos relatórios e metas.

---

## Sugestão de ordem (se for tocar)
0. ✅ **Dashboard & relatórios** (§3) — feito: CRUD/lista (2026-06-10) + editar transação, agilidade (FAB/atalho/sub-nav/filtros lembrados) e **relatório mensal com CSV** (2026-06-11). Restam refinamentos (PDF, filtros no relatório, tendência) nas "Novas recomendações" da §3.
1. **Cadastrar conta + desfazer no bot** (§1) — tira o atrito do dia a dia (o CRUD web já alivia o cadastro de conta, mas o "desfazer" no card ainda falta).
2. **MinIO atrás do Caddy** (§6) — destrava ver comprovante no site.
3. **Orçamento por categoria + alertas** (§4) — vira "organizador" de verdade, não só "registrador".
4. **Cron das recorrências** (§6) — automação que já está 90% pronta.
5. **Categorização automática + perguntas em linguagem natural** (§8) — o salto de "registrador" pra "copiloto"; alto valor percebido.
6. **Open Finance / importar fatura** (§9) — quando quiser matar o lançamento manual de vez.

> Cada item vira um (ou poucos) commits no padrão do projeto: 1 step = 1 commit,
> smoke test verde entre cada. Quando for pegar um, vale abrir um mini-plano no
> estilo dos docs de `AUTH_CONTINUACAO.md`.
