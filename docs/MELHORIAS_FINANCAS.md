# Melhorias pendentes — Agente Financeiro

Backlog **do que falta** no Organizador Financeiro — cardápio de ideias com
**prioridade sugerida** (🔴 alta / 🟡 média / 🟢 baixa) e o *porquê*.

> O que **já está pronto** saiu daqui pra `docs/FINANCAS_FEITO.md` (por
> categoria). Operação/handoff em `docs/CONTINUACAO.md`.

Última revisão: **2026-06-13**.

---

## 1. Bot do Telegram (onde você mais usa)

- 🟡 **Lançar despesa prevista / agendada** — *"vou pagar 200 de luz dia 10"* → cria como `prevista`. Hoje o bot só lança como `paga`.
- 🟡 **Resumo por período** — `/resumo julho`, `/resumo semana`, e "quanto gastei em mercado esse mês?".
- 🟡 **Confirmação mais rica** — no card, deixar trocar a **categoria** e a **conta** por botões (hoje só Confirmar/Cancelar/Editar).
- 🟢 **Atalhos de conta** — apelidos (`vr`, `nu`) configuráveis por usuário em vez de casar pelo nome/tipo.

## 2. Casal / multi-usuário

- 🟡 **Atribuição por pessoa (mantendo a carteira junta)** — gravar *quem* lançou (Pablo/Monique) mesmo caindo na mesma carteira, pra depois ver "quem gastou o quê". Hoje os dois viram o mesmo `usuario_id` e some essa informação.
- 🟡 **Renomear o "slot 2"** — as vars `TELEGRAM_*_SANDRA` são legado; trocar por algo neutro (`_2`) ou, melhor, um **mapa chat→usuário em tabela** (suporta N pessoas sem mexer no `.env`).
- 🟢 **Visão "individual vs casal"** — alternar no dashboard entre o consolidado e o de cada pessoa (depende da atribuição acima).

## 3. Dashboard web & relatórios

> Tudo o que estava aqui **saiu na leva de 2026-06-13** (export PDF, filtrar por
> conta/categoria, clicar no mês → lista, comparar com o ano anterior, busca
> global). Ver `FINANCAS_FEITO.md` §1. **Dark mode foi descartado** (decisão do
> Pablo — não vamos fazer).

- 🟢 **Evolução de saldo real (patrimônio no tempo)** — fica no **§10** (Patrimônio): o "saldo por mês" de hoje é o *resultado* (receitas − despesas); o patrimônio acumulado mês a mês precisa de snapshots (não guardamos histórico).

## 3b. Paridade backend ↔ tela (o backend já faz, a tela ainda não)

> Objetivo: poder fazer TUDO pela tela de Finanças. Estas funções **já existem
> no backend**, só falta a interface no front.

- 🟡 **Boleto parcelado na tela** — `POST /api/financas/compras/boleto` (`BoletoParceladoCreate`): boleto que vira N parcelas mensais (sem fatura). Ausente no front. (Ver também §3d.) *(Auto-split VR/VA e detalhe de compra parcelada já saíram — ver FEITO §3b.)*

## 3c. Boletos profissionais

- 🟡 **Detectar boleto recorrente e oferecer virar conta fixa** — hoje dá pra "tornar recorrente" na mão (botão ↻); falta o sistema **perceber** que um boleto se repete e sugerir. Cruza com o detector de assinaturas do §8.
- 🟢 **Não feitos (de propósito):** passo de revisão antes de criar (conflita com o "nunca some / auto-cria"), sanity checks (valor 0 / data improvável — baixo valor), histórico dedicado (os dados já aparecem no editor + anexos).

## 3d. Cartões profissionais

> Já saíram (ver `FINANCAS_FEITO.md` §3d): o trio que torna o cartão usável
> (lançar compra, extrato, pagar a fatura), a assinatura recorrente, o "pagar o
> mês", o atalho "Pagar fatura" no card, a **projeção consolidada**, o **estorno
> de compra** e a **auto-categoria por compra**. Falta:

- 🟡 **Boleto parcelado na tela** — `POST /api/financas/compras/boleto` já existe (boleto carnê → N parcelas, sem fatura); falta UI **e surfaçar/pagar as parcelas** (hoje a aba "A pagar" mostra `Transacao`, não `Parcela` de boleto — então o carnê some). É mais que um form.
- 🟢 **Ajustar valor de compra** — o **estorno** (cancelar a compra inteira) já saiu; falta editar o valor/parcelas de uma compra existente sem excluir e relançar.
- 🟢 **Antecipar parcelas** — pagar parcelas futuras adiantado e recalcular as faturas (mover parcela entre meses). O mais complexo do bloco.
- 🟢 **Importar a fatura (PDF/CSV)** — ler a fatura inteira do banco e gerar as compras/parcelas de uma vez, conciliando (§9). **O Pablo pediu pra pular por ora.**
- 🟢 **Anexar comprovante à compra/fatura** — igual ao boleto (depende do MinIO atrás do Caddy, §6).

## 4. Metas, orçamento e alertas (o "loop de gestão")

- 🟡 **Mais alertas no digest** — o alerta de **orçamento** acima de X% já saiu (FEITO §4) e os de **vencimento** (boleto/fatura) também; falta o "saldo previsto do mês ficaria negativo".
- 🟢 **Orçar por categoria-pai (roll-up de subcategorias)** — hoje o orçamento casa por categoria exata; somar os gastos das subcategorias num teto da categoria-mãe.
- 🟡 **Projeção de fim de mês** — com base nas recorrências previstas + média, dizer "sobra estimada: R$ Y".
- 🟢 **Reservas com objetivo** — meta de valor numa conta tipo reserva (ex.: "viagem: R$ 5.000") com barra de progresso.

## 5. Importador / IA

- 🟡 **Importar extrato bancário (OFX/CSV/PDF)** — conciliar muitos lançamentos de uma vez, não só boleto a boleto.
- 🟡 **Categorização automática** — sugerir a categoria pela descrição (aprende com o histórico), reduzindo o "Editar" no card. (Hoje o boleto já reaproveita por beneficiário; isto é o geral.)
- 🟢 **Ler comprovante PIX / nota fiscal** — estender o importador além de boleto.

## 6. Confiabilidade & infraestrutura

- 🔴 **Expor o MinIO atrás do Caddy** — pra as imagens de comprovante **abrirem no navegador** (hoje a URL presignada aponta pro `minio:9000`, inacessível ao browser). Inclui ajustar `S3_ENDPOINT` público + `img-src` do CSP.
- 🟡 **Monitoramento/alerta de saúde** — ping no `/api/health` + aviso se a API cair; checar o cron de backup.
- 🟡 **Testes E2E / verificação visual (Playwright)** — hoje a validação de tela é manual (a API/lógica têm smoke tests, o front não). Um Playwright que faz login e tira screenshot/roda smoke das telas dá pra conferir mudanças de UI sem subir e clicar à mão.
- 🟢 **Testar o restore do backup** — restaurar um dump num banco de teste e confirmar que volta inteiro.
- 🟢 **Observabilidade** — logs estruturados + métricas (lançamentos/dia, latência do importador).

## 7. Segurança & dados

- 🟡 **2FA obrigatório pro admin** — hoje é opcional; tornar exigido pra quem tem `usuarios.gerenciar`.
- 🟢 **Exportar meus dados** — botão "baixar tudo" (LGPD-friendly), CSV/JSON de transações.
- 🟢 **Trilha de auditoria no front** — visualizar os eventos de segurança (login, troca de senha, 2FA) numa tela.

## 8. Inteligência do agente (de registrador a copiloto)

O módulo registra bem; o salto é ele **entender e antecipar**. Território de IA
(Gemini/Groq, já no stack) + as consultas que já existem.

- 🔴 **Perguntas em linguagem natural sobre os dados** — *"quanto gastei com mercado nos últimos 3 meses?"*, *"qual meu maior gasto de junho?"*. Um agente com *tool calling* sobre os endpoints de resumo/transações responde sem o usuário virar relatório. Vale no dashboard e no bot.
- 🔴 **Categorização automática que aprende** — sugerir a categoria pela descrição usando o histórico do próprio usuário (confirmar com 1 toque). Reduz o atrito de lançar.
- 🟡 **Insights proativos (digest)** — resumo semanal/mensal automático no Telegram: "essa semana você gastou R$ X (−12% vs. média), top categoria: delivery".
- 🟡 **Detector de assinaturas/recorrências não cadastradas** — achar cobranças que se repetem ("parece que você paga Spotify todo mês — quer cadastrar como conta fixa?").
- 🟡 **Alerta de anomalia** — gasto muito fora do padrão da categoria/mês dispara um aviso ("R$ 800 em farmácia, 4x sua média").
- 🟢 **Áudio no bot** — mandar um áudio ("gastei trinta no uber") → transcrição (Whisper/Groq) → NLU → card.
- 🟢 **Coach de metas** — quando houver orçamento (§4), o agente comenta o ritmo ("no dia 10 você já usou 60% do teto de mercado").

## 9. Integrações bancárias (matar o lançamento manual)

- 🔴 **Open Finance (Pluggy/Belvo)** — conectar a conta/cartão e importar transações automaticamente, com conciliação contra o que já foi lançado. É o "santo graal".
- 🟡 **Importar fatura de cartão (PDF/CSV)** — ler a fatura inteira e gerar as compras/parcelas de uma vez, conciliando.
- 🟡 **Ler comprovante de PIX / nota fiscal** — estender o importador pra PIX e NF (QR/imagem).

## 10. Patrimônio e planejamento (além do fluxo de caixa)

- 🟡 **Patrimônio líquido** — somar contas + reservas − dívidas (faturas/parcelas em aberto) e acompanhar a evolução mês a mês.
- 🟢 **Investimentos** — registrar aportes/saldo de investimentos (mesmo manual) pra ter a foto completa.
- 🟢 **Relatório anual / IRPF** — consolidado do ano por categoria, exportável.
- 🟢 **Multi-perfil/visão** — quando a atribuição por pessoa (§2) existir, alternar entre "casal" e "Pablo/Monique" nos relatórios e metas.

---

## Sugestão de ordem (se for tocar)

1. ✅ ~~Cadastrar conta + desfazer no bot (§1)~~ — **feito** (`/conta`, `/contas`, `/desfazer`).
2. **MinIO atrás do Caddy** (§6) — destrava ver comprovante no site.
3. **Orçamento por categoria + alertas** (§4) — vira "organizador" de verdade.
4. **Boleto parcelado + projeção/limite/lembrete de fatura** (§3d) — fecha o cartão.
5. **Categorização automática + perguntas em linguagem natural** (§8) — o salto de "registrador" pra "copiloto".
6. **Open Finance / importar fatura** (§9) — quando quiser matar o lançamento manual de vez.

> Cada item vira um (ou poucos) commits no padrão do projeto: 1 step = 1 commit,
> smoke test verde entre cada.
