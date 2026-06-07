# RUNBOOK — Subir a stack no VPS Hetzner CX32

Objetivo: você compra o CX32, segue isto de cima a baixo, e termina com tudo no ar
(Postgres, MinIO, HTTPS automático e os ganchos prontos pro Prospector e pro
Organizador Financeiro). Sem improviso na hora.

**Legenda:**
- 🟦 `[CLAUDE CODE]` — o Claude Code prepara/verifica no repo, antes do VPS existir.
- 🟨 `[VOCÊ — MANUAL]` — coisas que só você pode fazer (pagar, painel, tokens).
- 🟩 `[NO VPS]` — comandos rodados dentro do servidor por SSH.

> Por que Caddy e não Nginx+Certbot: o Caddy emite e renova o HTTPS sozinho.
> Menos peça pra quebrar num setup "subir e esquecer". Já vem configurado aqui.

---

## Visão geral dos arquivos (já prontos neste pacote)

```
deploy/
├── docker-compose.yml          # postgres + minio + caddy + api + web
├── .env.example                # template de segredos (copie p/ .env)
├── .gitignore                  # ignora .env, backups, logs
├── api.Dockerfile              # imagem da API FastAPI
├── web.Dockerfile              # imagem do front Next.js
├── caddy/
│   └── Caddyfile               # HTTPS automático + roteamento
└── scripts/
    ├── 01-bootstrap.sh         # hardening + docker (roda 1x como root)
    ├── 02-deploy.sh            # sobe/atualiza a stack
    ├── backup.sh               # dump diário do Postgres (cron)
    └── set-telegram-webhook.sh # registra o webhook do bot
```

---

## ETAPA 0 — 🟦 `[CLAUDE CODE]` Preparar o repo

1. Copiar a pasta `deploy/` para a raiz do repo do Prospector.
2. Garantir que `deploy/.env` está no `.gitignore` (já está).
3. Conferir que `scripts/*.sh` têm permissão de execução:
   `chmod +x deploy/scripts/*.sh`
4. Commitar: **1 commit** — "infra: pacote de deploy do VPS (compose, caddy, scripts)".

> Os serviços `api` e `web` no compose só vão *buildar* quando o código FastAPI/Next
> existir. Até lá, sobe-se só a infra (Etapa 5, modo `infra`). Isso é esperado.

---

## ETAPA 1 — 🟨 `[VOCÊ — MANUAL]` Comprar e criar o servidor

1. Cria conta na **Hetzner Cloud** (console.hetzner.cloud).
2. **Adiciona sua chave SSH pública** no projeto (Security → SSH Keys).
   - Se não tem chave: `ssh-keygen -t ed25519` na sua máquina; a pública é `~/.ssh/id_ed25519.pub`.
3. Cria o servidor:
   - Tipo: **CX32** (4 vCPU, 8 GB RAM)
   - Imagem: **Ubuntu 24.04**
   - Região: qualquer (Falkenstein/Nuremberg é o padrão; latência BR não é crítica aqui)
   - SSH key: marca a sua
4. Anota o **IP público**.

---

## ETAPA 2 — 🟨 `[VOCÊ — MANUAL]` DNS, tokens e chaves

Pré-requisitos pro HTTPS e pro bot funcionarem. Reúna tudo antes de subir:

1. **Subdomínio** apontando pro VPS: cria um registro **A** no seu domínio
   (ex.: `financas.seudominio.com.br → IP_DO_VPS`). Espera propagar (uns minutos).
2. **Bot do Telegram**: fala com o **@BotFather** → `/newbot` → guarda o **token**.
3. **Seu chat_id** (e o da Sandra): fala com o **@userinfobot** → guarda os números.
4. **Chaves de LLM**: `GEMINI_API_KEY` (Google AI Studio) e `GROQ_API_KEY` (console.groq.com).
5. Gera segredos: `openssl rand -base64 24` (senhas) e `openssl rand -hex 16` (webhook secret).

---

## ETAPA 3 — 🟩 `[NO VPS]` Bootstrap (uma vez, como root)

```bash
ssh root@SEU_IP
# manda o script pro servidor (ou cola o conteúdo):
#   scp deploy/scripts/01-bootstrap.sh root@SEU_IP:~
bash 01-bootstrap.sh
```

O script faz: usuário `deploy`, hardening de SSH, firewall (22/80/443),
fail2ban, swap 4 GB, timezone SP, patches automáticos, Docker + compose.

⚠️ **Antes de fechar o root**, abre OUTRO terminal e testa:
```bash
ssh deploy@SEU_IP
```
Logou? Beleza. Não logou? Mantém o root aberto e revê a chave SSH (Etapa 1.2).

---

## ETAPA 4 — 🟩 `[NO VPS]` Trazer o repo e preencher o .env

Como usuário `deploy`:
```bash
# opção A: clonar (repo privado → configura deploy key ou usa token)
git clone SEU_REPO ~/reative
# opção B: copiar da sua máquina
#   scp -r ./reative deploy@SEU_IP:~/

cd ~/reative/deploy
cp .env.example .env
nano .env        # preenche DOMAIN, senhas, chaves, token do bot, chat_ids
```

---

## ETAPA 5 — 🟩 `[NO VPS]` Subir a INFRA

Enquanto o app financeiro ainda não foi codado, sobe só a base:
```bash
cd ~/reative/deploy
./scripts/02-deploy.sh infra
```

Confere:
```bash
docker compose ps          # postgres, minio, caddy devem estar 'running'/'healthy'
```

Abre `https://SEU_DOMINIO` no navegador. O Caddy vai emitir o certificado na
primeira visita (pode levar alguns segundos). Vai dar 502 no front (normal —
ainda não tem app). O importante: **cadeado verde = HTTPS funcionando.**

---

## ETAPA 6 — 🟩 `[NO VPS]` Backup automático

```bash
crontab -e
# adiciona:
0 3 * * * /home/deploy/reative/deploy/scripts/backup.sh >> /home/deploy/backup.log 2>&1
```
Dump diário às 3h, rotação de 14 dias em `~/backups`.
**Teste o restore uma vez** antes de confiar (backup que nunca foi restaurado não é backup).

---

## ETAPA 7 — depois, conforme você desenvolve o módulo `financas`

(Estes passos acontecem ao longo dos 30 commits do outro plano — não agora.)

1. 🟦 `[CLAUDE CODE]` Código FastAPI com `requirements.txt`, `alembic`, entrypoint
   `app.main:app`, e o endpoint `POST /telegram/webhook`. Front Next com
   `output: 'standalone'` no `next.config.js`.
2. 🟩 `[NO VPS]` Sobe a stack completa:
   ```bash
   cd ~/reative/deploy && ./scripts/02-deploy.sh
   ```
3. 🟩 `[NO VPS]` Registra o webhook do bot (só depois do HTTPS ok):
   ```bash
   ./scripts/set-telegram-webhook.sh
   ```
4. 🟩 Cria os buckets no MinIO (`comprovantes`, `boletos`, `notas`). Acesso ao
   console via túnel SSH (não fica exposto):
   ```bash
   ssh -L 9001:localhost:9001 deploy@SEU_IP
   # abre http://localhost:9001 no seu navegador, loga com MINIO_ROOT_*
   ```

---

## Operação do dia a dia

| Ação | Comando (no VPS, em `~/reative/deploy`) |
|---|---|
| Atualizar após novo commit | `./scripts/02-deploy.sh` |
| Ver logs da API | `docker compose logs -f api` |
| Reiniciar um serviço | `docker compose restart api` |
| Status geral | `docker compose ps` |
| Backup manual | `./scripts/backup.sh` |
| Uso de recursos | `docker stats` |

---

## Lembrete de fronteira GPU
Nada de Chatterbox TTS / BGE reranker / Ollama neste VPS — sem GPU, inviável.
O VPS roda o que é CPU + cloud-LLM (Prospector, financas, bots, dashboards).
A parte pesada do Content Factory **fica na RTX 2060**, acionada por fila quando precisar.

---

## Checklist final (tudo verde = pronto)
- [ ] CX32 criado, IP anotado, chave SSH funcionando
- [ ] Subdomínio (A record) apontando pro IP
- [ ] Token do bot, chat_ids, chaves Gemini/Groq em mãos
- [ ] `01-bootstrap.sh` rodado; login como `deploy` confirmado
- [ ] `.env` preenchido
- [ ] Infra no ar (`docker compose ps` healthy)
- [ ] `https://SEU_DOMINIO` com cadeado verde
- [ ] Cron de backup ativo e restore testado
