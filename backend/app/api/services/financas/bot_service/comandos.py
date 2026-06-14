"""Comandos diretos do bot: /saldo, /resumo, /contas, /conta, /desfazer,
/gasto e /ganho."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.api.schemas.financas import ContaCreate, DespesaCreate, ReceitaCreate
from app.api.services.financas import conta_service, resumo_service, transacao_service
from app.api.services.financas.conta_service import ContaError
from app.api.services.financas.transacao_service import TransacaoError
from app.db.models.financas.conta import TIPOS_CONTA

from ._base import _parse_periodo, _responder


async def _saldos(chat_id: str, usuario_id: str) -> dict:
    contas = (await conta_service.listar_contas(usuario_id, apenas_ativas=True)).items
    if not contas:
        await _responder(chat_id, "Você ainda não tem contas cadastradas.")
        return {"ok": True, "consulta": "saldo"}
    linhas = [f"• {c.nome}: R$ {c.saldo_atual}" for c in contas]
    total = sum(Decimal(c.saldo_atual) for c in contas)
    await _responder(chat_id, "🏦 <b>Saldos</b>\n" + "\n".join(linhas) + f"\n\n<b>Total:</b> R$ {total}")
    return {"ok": True, "consulta": "saldo"}


async def _resumo_mes(chat_id: str, usuario_id: str, texto: str = "") -> dict:
    arg = texto.split(maxsplit=1)[1] if len(texto.split(maxsplit=1)) > 1 else ""
    ano, mes = _parse_periodo(arg)
    r = await resumo_service.resumo_mes(usuario_id, ano, mes)
    sinal = "🟢" if r.saldo >= 0 else "🔴"
    linhas = [
        f"📊 <b>{r.mes:02d}/{r.ano}</b>",
        f"💰 Receitas: R$ {r.total_receitas}",
        f"💸 Despesas: R$ {r.total_despesas}",
        f"{sinal} Sobra/Déficit: R$ {r.saldo}",
    ]
    if r.por_categoria:
        linhas.append("\n<b>Maiores categorias:</b>")
        for c in r.por_categoria[:3]:
            linhas.append(f"• {c.categoria_nome}: R$ {c.total}")
    await _responder(chat_id, "\n".join(linhas))
    return {"ok": True, "consulta": "resumo"}


async def _listar_contas(chat_id: str, usuario_id: str) -> dict:
    contas = (await conta_service.listar_contas(usuario_id, apenas_ativas=True)).items
    if not contas:
        await _responder(
            chat_id,
            "Você ainda não tem contas.\n"
            "Crie uma com <code>/conta Nubank corrente</code>.",
        )
        return {"ok": True, "comando": "contas", "total": 0}
    linhas = [f"• <b>{c.nome}</b> ({c.tipo}): R$ {c.saldo_atual}" for c in contas]
    await _responder(chat_id, "🏦 <b>Suas contas</b>\n" + "\n".join(linhas))
    return {"ok": True, "comando": "contas", "total": len(contas)}


async def _cmd_conta(chat_id: str, usuario_id: str, texto: str) -> dict:
    """Cria uma conta: /conta <nome…> [tipo]. O último token vira o tipo se for
    um tipo válido; senão tudo é o nome e o tipo cai pra 'corrente'."""
    args = texto.split()[1:]
    if not args:
        await _responder(
            chat_id,
            "Uso: <code>/conta &lt;nome&gt; [tipo]</code>\n"
            "Ex.: <code>/conta Nubank corrente</code>\n"
            f"Tipos: {', '.join(TIPOS_CONTA)} (padrão: corrente).",
        )
        return {"ok": True, "comando": "conta", "erro": "uso"}

    tipo = "corrente"
    if len(args) > 1 and args[-1].lower() in TIPOS_CONTA:
        tipo = args[-1].lower()
        args = args[:-1]
    nome = " ".join(args)

    try:
        conta = await conta_service.criar_conta(
            ContaCreate(usuario_id=usuario_id, nome=nome, tipo=tipo)
        )
    except ContaError as e:
        await _responder(chat_id, f"🤔 {e}")
        return {"ok": True, "comando": "conta", "erro": "negocio"}

    await _responder(
        chat_id,
        f"✅ Conta criada: <b>{conta.nome}</b> ({conta.tipo}).\n"
        "Já dá pra lançar nela.",
    )
    return {"ok": True, "comando": "conta", "conta_id": conta.id}


async def _cmd_desfazer(chat_id: str, usuario_id: str) -> dict:
    """Apaga o último lançamento criado (revertendo o saldo, se estava pago)."""
    ultima = await transacao_service.ultima_transacao(usuario_id)
    if ultima is None:
        await _responder(chat_id, "Não tem nada pra desfazer 🤷")
        return {"ok": True, "comando": "desfazer", "nada": True}
    try:
        await transacao_service.excluir_transacao(ultima.id)
    except TransacaoError as e:
        await _responder(chat_id, f"🤔 {e}")
        return {"ok": True, "comando": "desfazer", "erro": "negocio"}
    await _responder(
        chat_id,
        f"↩️ Desfeito: <b>{ultima.descricao}</b> R$ {ultima.valor_total}.",
    )
    return {"ok": True, "comando": "desfazer", "transacao_id": ultima.id}


async def _cmd_lancar(chat_id: str, usuario_id: str, texto: str, *, tipo: str) -> dict:
    """Lança rápido despesa (/gasto) ou receita (/ganho): <valor> <descrição> [conta]."""
    eh_receita = tipo == "receita"
    cmd = "/ganho" if eh_receita else "/gasto"
    rotulo = "ganho" if eh_receita else "gasto"

    partes = texto.split()
    if len(partes) < 3:
        exemplo = "/ganho 2000 salário" if eh_receita else "/gasto 50 mercado"
        await _responder(
            chat_id,
            f"Uso: <code>{cmd} &lt;valor&gt; &lt;descrição&gt; [conta]</code>\n"
            f"Ex.: <code>{exemplo}</code>",
        )
        return {"ok": True, "comando": rotulo, "erro": "uso"}

    try:
        valor = Decimal(partes[1].replace(",", "."))
    except InvalidOperation:
        await _responder(chat_id, f"Valor inválido: {partes[1]!r}")
        return {"ok": True, "comando": rotulo, "erro": "valor"}
    if valor <= 0:
        await _responder(chat_id, "O valor precisa ser maior que zero.")
        return {"ok": True, "comando": rotulo, "erro": "valor"}

    resto = partes[2:]
    contas = (await conta_service.listar_contas(usuario_id, apenas_ativas=True)).items
    if not contas:
        await _responder(chat_id, "Você ainda não tem contas. Cadastre uma primeiro.")
        return {"ok": True, "comando": rotulo, "erro": "sem_conta"}

    # Último token pode ser o nome/tipo de uma conta.
    conta = None
    if len(resto) > 1:
        cand = resto[-1].lower()
        for c in contas:
            if cand == c.nome.lower() or cand == c.tipo.lower():
                conta = c
                resto = resto[:-1]
                break
    if conta is None:
        conta = contas[0]  # default: primeira conta ativa

    descricao = " ".join(resto) or rotulo
    if eh_receita:
        resp = await transacao_service.lancar_receita(ReceitaCreate(
            usuario_id=usuario_id, descricao=descricao,
            valor_total=valor, conta_id=conta.id,
        ))
        await _responder(
            chat_id,
            f"💰 Entrou R$ {valor}: <b>{descricao}</b> na conta <b>{conta.nome}</b>.",
        )
    else:
        resp = await transacao_service.lancar_despesa(DespesaCreate(
            usuario_id=usuario_id, descricao=descricao,
            valor_total=valor, conta_id=conta.id,
        ))
        await _responder(
            chat_id,
            f"✅ R$ {valor} em <b>{descricao}</b> na conta <b>{conta.nome}</b>.",
        )
    return {"ok": True, "comando": rotulo, "transacao_id": resp.id, "conta": conta.nome}
