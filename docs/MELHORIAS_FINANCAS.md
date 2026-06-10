# Melhorias possíveis — Agente Financeiro

Backlog de evolução do Organizador Financeiro. Não é obrigação — é um cardápio
de ideias, com **prioridade sugerida** (🔴 alta / 🟡 média / 🟢 baixa) e o
*porquê*. O módulo hoje já cobre o essencial (contas, categorias, despesas/
receitas, cartões/parcelas, recorrências, consumo, comprovantes, importador de
boleto por IA, NLU, bot e dashboard ao vivo). O que falta é, sobretudo,
**fechar o loop de gestão** (orçar, alertar, relatar) e polir as bordas.

Última revisão: 2026-06-10.

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

- ✅ **CRUD de conta, categoria e transação no front** (2026-06-10) — criar/editar/excluir **conta** e **categoria** por modal, e **lançar despesa/receita** + **excluir** transação (com reversão de saldo) pela interface. Falta ainda CRUD de **cartão** e **recorrência**.
- ✅ **Lista de transações filtrável** (2026-06-10) — por mês, conta, categoria, tipo e busca na descrição. Edição é por excluir + relançar (não há edição inline ainda).
- 🟡 **Relatório mensal** — comparativo mês a mês, evolução de saldo, top categorias, exportar PDF/CSV.
- 🟢 **Detalhe de cartão** — extrato da fatura, parcelas futuras, projeção de quanto vai pesar nos próximos meses.

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

## 7. Segurança & dados

- 🟡 **2FA obrigatório pro admin** — hoje é opcional; tornar exigido pra quem tem `usuarios.gerenciar`.
- 🟢 **Exportar meus dados** — botão "baixar tudo" (LGPD-friendly), CSV/JSON de transações.
- 🟢 **Trilha de auditoria no front** — visualizar os eventos de segurança (login, troca de senha, 2FA) numa tela.

---

## Sugestão de ordem (se for tocar)
1. **Cadastrar conta + desfazer no bot** (§1) — tira o atrito do dia a dia.
2. **MinIO atrás do Caddy** (§6) — destrava ver comprovante no site.
3. **Orçamento por categoria + alertas** (§4) — vira "organizador" de verdade, não só "registrador".
4. **CRUD no front + lista de transações** (§3) — autonomia sem depender de API/bot.
5. **Cron das recorrências** (§6) — automação que já está 90% pronta.

> Cada item vira um (ou poucos) commits no padrão do projeto: 1 step = 1 commit,
> smoke test verde entre cada. Quando for pegar um, vale abrir um mini-plano no
> estilo dos docs de `AUTH_CONTINUACAO.md`.
