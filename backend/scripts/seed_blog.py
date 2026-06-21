"""Migra os posts hardcoded do site (`lib/content/posts.tsx` + `home.ts`) pro
banco do studio — prova o cano headless ponta a ponta (P5 §6.B0).

Idempotente: faz upsert por slug. Roda com:
    python -m scripts.seed_blog
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.api.services import blog_service as svc
from app.db.session import get_session
from app.repositories.blog_repository import BlogRepository

# ── Post 1 (real, convertido de JSX → Markdown GFM) ──────────────
_PLANILHA = """\
Se você é dono de PME, é bem provável que tenha pelo menos uma planilha que **ninguém pode mexer sem perguntar antes.** Aquela que controla o estoque, ou os pedidos, ou a comissão da equipe comercial. Aquela que se quebrar num sábado de manhã, atrasa a entrega de segunda.

Planilha é uma ferramenta incrível pra começar. O problema é que ela cresce sem avisar — e quando você percebe, ela *já virou um sistema*. Só que sem backup, sem controle de acesso, sem histórico de mudança e sem suporte.

Este artigo é sobre os 5 sinais que indicam que chegou a hora de tirar o seu negócio do Excel. Se você marcar 3 ou mais, dá pra começar a conversa.

## 1. Mais de uma pessoa precisa editar ao mesmo tempo

"Fulana, fecha aí que eu preciso lançar o pedido." Se essa frase é frequente no seu dia, sua planilha **já não é uma planilha** — é um banco de dados mal-tratado.

Mesmo no Google Sheets ou no Excel online, edição simultânea quebra fórmulas, sobrescreve linhas e gera "versões fantasma" que ninguém sabe qual é a verdadeira. Sistema de verdade resolve isso com transações — uma pessoa por vez salva, mas ninguém precisa esperar.

> **Sinal de alerta:** se você já perdeu pelo menos um pedido por causa de "duas pessoas mexeram ao mesmo tempo", você já pagou o preço de não ter sistema. Provavelmente várias vezes.

## 2. Tem fórmula que ninguém mais entende

A planilha foi construída pelo João, que saiu da empresa em 2023. Tem uma célula no canto direito que faz `=PROCV(SE(...))` em três abas, multiplica por uma constante chamada `FATOR_X`, e ninguém ousa mexer porque uma vez mexeram e o fechamento do mês quebrou.

Isso é **dívida técnica.** Acontece com sistema também — mas em sistema bem feito, a regra fica documentada e auditável. Em planilha, a regra mora numa célula, sem teste, sem versionamento, sem dono.

> "Toda fórmula complexa em planilha é uma bomba-relógio. Você não sabe quando explode — só sabe que vai explodir, e provavelmente no pior dia possível."

## 3. Você manda print pra confirmar valor

Sabe quando o vendedor pergunta "o desconto é 7% ou 10% pro cliente X?" e você abre a planilha, dá um print da célula e manda no WhatsApp dele?

Isso significa que o **dado certo está na sua cabeça ou no seu acesso**, e a planilha é só um lembrete pra você. Em sistema, cada usuário vê o valor certo do lugar onde ele vai usar — e ninguém precisa parar o que está fazendo pra confirmar.

## 4. Tem cópia "de backup" toda semana

```text
vendas_2026.xlsx
vendas_2026_backup.xlsx
vendas_2026_backup_NOVO.xlsx
vendas_2026_FINAL.xlsx
vendas_2026_FINAL_v2_NÃO_MEXER.xlsx
```

Se isso te lembra a sua pasta no Drive, você está fazendo backup manual porque **não confia que a versão atual está protegida.** E está certo de não confiar — planilha não tem rollback, não tem auditoria, não tem histórico confiável.

### Por que backup manual não é backup

- Você só tem o que copiou na hora — entre cópias, está descoberto.
- Se você apagar uma linha errada e salvar, a cópia anterior não te ajuda se já é da semana passada.
- Se a planilha corromper, você descobre na próxima vez que abrir — pode ser meses depois.
- Ninguém testa o backup. Quando precisa, descobre que não funciona.

## 5. Travou — e a operação parou

O sinal mais claro de todos: na semana passada, a planilha não abriu. Ou abriu com erro. Ou alguém apagou uma aba sem querer. E nesse intervalo, **sua empresa não conseguiu trabalhar.**

Se a planilha tem esse poder, ela é infraestrutura crítica. Infraestrutura crítica precisa de monitoramento, redundância e um plano de recuperação. Tudo o que planilha não tem.

---

## Tá, e o próximo passo?

A boa notícia: **tirar o negócio da planilha não significa contratar um sistema gigante de R$ 5 mil/mês.** Na maioria dos casos, dá pra resolver com uma combinação enxuta de:

- Um banco de dados leve (Supabase, Airtable, ou até Google Sheets como API).
- Uma interface simples pra equipe lançar e consultar.
- Automações pra reduzir o trabalho manual repetitivo.
- Backup automatizado e controle de quem mexeu no quê.

O custo de fazer isso bem feito é bem menor do que o custo de continuar improvisando — e fica mais barato quanto antes começar.
"""

_SITE_LENTO = """\
Site bonito vende uma primeira impressão. Site rápido vende todo dia. E quando os dois brigam por orçamento, é o desempenho que costuma trazer mais retorno — porque cada segundo a mais de carregamento derruba a conversão.

## A conta que ninguém faz

Quando uma página demora pra abrir, parte das visitas desiste antes de ver qualquer coisa. Não importa quão bonito é o layout que não chegou a carregar. O visitante volta pro Google e clica no concorrente — que talvez tenha um site mais simples, porém mais rápido.

## Onde o tempo se perde

- **Imagens pesadas** servidas no tamanho original, sem compressão nem formato moderno.
- **Excesso de scripts** de terceiros (chats, pixels, banners) carregando antes do conteúdo.
- **Hospedagem barata** que responde devagar sob qualquer pico de acesso.
- **Falta de cache**, refazendo todo o trabalho a cada visita.

## O que dá pra fazer

Performance não é luxo de site grande — é higiene básica. Otimizar imagens, adiar o que não é essencial, usar uma boa hospedagem e medir o tempo real de carregamento já coloca o seu site à frente da maioria. O bonito continua bonito; só que agora ele aparece a tempo de converter.
"""

_SEM_TI = """\
A conta de ter suporte de TI parece alta — até você somar quanto custa **não** ter. O gasto invisível não aparece numa fatura, mas aparece em horas paradas, dados perdidos e oportunidades que escaparam.

## O custo invisível

- **Equipe parada** quando o sistema cai e ninguém sabe a quem ligar.
- **Backup que nunca foi testado** — e que falha justamente no dia em que era preciso.
- **Brechas de segurança** que só viram urgência depois do incidente.
- **Decisões no escuro** porque os dados estão espalhados e desatualizados.

## Reativo sai mais caro que preventivo

Resolver problema depois que ele estourou é sempre mais caro do que evitá-lo. Suporte de TI bem feito é manutenção contínua: monitorar, atualizar, fazer backup de verdade e ter alguém de prontidão quando algo sai do lugar.

## O ponto de partida

Não precisa de um departamento inteiro. Precisa de processo: saber o que é crítico no seu negócio, garantir que está protegido e ter um plano claro pra quando algo falhar. O resto é consequência.
"""


_POSTS: list[dict[str, Any]] = [
    dict(
        slug="planilha-virou-sistema",
        title="5 sinais de que a sua planilha já virou sistema (e ninguém percebeu)",
        excerpt=(
            "Toda planilha começa simples. O problema é quando ela vira o coração "
            "da operação, tem 18 abas, ninguém entende as fórmulas — e o autor "
            "pediu férias."
        ),
        category="Automação",
        cover_class="post-cover-1",
        body_md=_PLANILHA,
        keyword_alvo="tirar empresa da planilha",
        meta_description=(
            "5 sinais de que sua planilha virou um sistema crítico — e a hora de "
            "tirar a operação do Excel sem gastar uma fortuna."
        ),
        published_at=datetime(2026, 5, 12, tzinfo=UTC),
    ),
    dict(
        slug="site-lento-custa-caro",
        title="Por que site lento custa mais caro que site bonito",
        excerpt=(
            "Cada segundo a mais de carregamento corta conversão. Mostramos por "
            "que desempenho rende mais que estética."
        ),
        category="Site",
        cover_class="post-cover-2",
        body_md=_SITE_LENTO,
        keyword_alvo="site lento perde venda",
        meta_description=(
            "Site lento derruba conversão e custa mais que site bonito. Onde o "
            "tempo se perde e o que dá pra fazer."
        ),
        published_at=datetime(2026, 4, 28, tzinfo=UTC),
    ),
    dict(
        slug="quanto-custa-nao-ter-ti",
        title="Quanto custa NÃO ter suporte de TI na sua PME",
        excerpt=(
            "A conta da TI parece alta — até a primeira invasão, o primeiro backup "
            "perdido ou o primeiro dia inteiro com a equipe parada."
        ),
        category="Gestão de TI",
        cover_class="post-cover-3",
        body_md=_SEM_TI,
        keyword_alvo="custo de não ter suporte de TI",
        meta_description=(
            "O custo invisível de não ter suporte de TI numa PME: equipe parada, "
            "backup que falha e brechas de segurança. Como começar."
        ),
        published_at=datetime(2026, 4, 14, tzinfo=UTC),
    ),
]


async def main() -> None:
    async with get_session() as session:
        repo = BlogRepository(session)
        for dados in _POSTS:
            dados = dict(dados)
            dados.setdefault("status", "publicado")
            dados.setdefault("author", "Equipe Reative")
            dados["word_count"] = svc.contar_palavras(dados["body_md"])
            dados["reading_time"] = svc.tempo_de_leitura(dados["body_md"])
            existente = await repo.get_por_slug(dados["slug"])
            if existente:
                await repo.update(existente.id, dados)
                print(f"  atualizado: {dados['slug']}")
            else:
                await repo.create(dados)
                print(f"  criado:     {dados['slug']}")
    print("✅ seed do blog concluído")


if __name__ == "__main__":
    asyncio.run(main())
