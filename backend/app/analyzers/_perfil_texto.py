"""Renderiza o Perfil Mestre em texto compacto pra entrar no prompt.

Usado tanto no match vaga×perfil quanto na geração de candidatura.
"""
from __future__ import annotations

from app.api.schemas.pessoal import PerfilMestreResponse


def perfil_para_texto(perfil: PerfilMestreResponse) -> str:
    linhas: list[str] = ["PERFIL MESTRE DO CANDIDATO:"]

    if perfil.titulo:
        linhas.append(f"Título: {perfil.titulo}")
    linhas.append(f"Nome: {perfil.nome}")
    if perfil.resumo:
        linhas.append(f"Resumo: {perfil.resumo}")

    if perfil.habilidades:
        linhas.append("\nHabilidades técnicas (nível — onde usou):")
        for h in perfil.habilidades:
            nivel = f" — {h.nivel}" if h.nivel else ""
            onde = f" ({h.onde_usou})" if h.onde_usou else ""
            linhas.append(f"- {h.nome}{nivel}{onde}")

    if perfil.projetos:
        linhas.append("\nProjetos (o que cada um prova):")
        for p in perfil.projetos:
            stack = f" [stack: {', '.join(p.stack)}]" if p.stack else ""
            prova = f" — prova: {p.prova}" if p.prova else ""
            desc = f" — {p.descricao}" if p.descricao else ""
            linhas.append(f"- {p.nome}{desc}{prova}{stack}")

    if perfil.experiencias:
        linhas.append("\nExperiência:")
        for e in perfil.experiencias:
            cargo = e.cargo or ""
            empresa = f" @ {e.empresa}" if e.empresa else ""
            periodo = f" ({e.periodo})" if e.periodo else ""
            desc = f" — {e.descricao}" if e.descricao else ""
            linhas.append(f"- {cargo}{empresa}{periodo}{desc}")

    if perfil.formacao:
        linhas.append("\nFormação:")
        for f in perfil.formacao:
            curso = f.curso or ""
            inst = f" — {f.instituicao}" if f.instituicao else ""
            periodo = f" ({f.periodo})" if f.periodo else ""
            linhas.append(f"- {curso}{inst}{periodo}")

    if perfil.certificacoes:
        linhas.append("\nCertificações (o que cada uma comprova):")
        for c in perfil.certificacoes:
            tema = f" [{c.tema}]" if c.tema else ""
            inst = f" — {c.instituicao}" if c.instituicao else ""
            ano = f" ({c.ano})" if c.ano else ""
            prova = f" — comprova: {c.prova}" if c.prova else ""
            linhas.append(f"- {c.nome}{tema}{inst}{ano}{prova}")

    if perfil.o_que_procuro:
        q = perfil.o_que_procuro
        partes = []
        if q.stack:
            partes.append(f"stack desejada: {', '.join(q.stack)}")
        if q.modelo:
            partes.append(f"modelo: {q.modelo}")
        if q.tipo_empresa:
            partes.append(f"tipo de empresa: {q.tipo_empresa}")
        if q.observacoes:
            partes.append(q.observacoes)
        if partes:
            linhas.append("\nO que procura: " + "; ".join(partes))

    return "\n".join(linhas)


def blocos_curriculo_para_texto(perfil: PerfilMestreResponse) -> str:
    """Lista os blocos reutilizáveis de currículo, se houver."""
    if not perfil.blocos_curriculo:
        return ""
    linhas = ["\nBLOCOS DE CURRÍCULO REUTILIZÁVEIS (use como matéria-prima):"]
    for b in perfil.blocos_curriculo:
        tags = f" [tags: {', '.join(b.tags)}]" if b.tags else ""
        linhas.append(f"- {b.titulo}{tags}: {b.conteudo}")
    return "\n".join(linhas)
