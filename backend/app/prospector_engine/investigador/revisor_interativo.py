from typing import Optional

from app.prospector_engine.investigador.confianca import Investigacao

def _icon_score(score: int) -> str:
    if score >= 85:
        return "✅"
    if score >= 65:
        return "🟢"
    if score >= 40:
        return "🟡"
    return "🟠"


def imprimir_resumo(inv: Investigacao) -> None:

    print()
    print("═" * 70)
    print("📋 RESUMO DA INVESTIGAÇÃO")
    print("═" * 70)

    campos = inv.campos_com_score()
    if not campos:
        print("⚠️  Nenhum dado coletado.")
        print("═" * 70)
        return

    for campo, (valor, score, fontes) in campos.items():
        icon = _icon_score(score)

        valor_curto = valor if len(valor) <= 55 else valor[:52] + "..."
        print(f"  {icon}  {campo:<18} {score:>3}%  {valor_curto}")
        print(f"      {'':<18}      fontes: {fontes}")

    if inv.socios:
        print()
        print(f"  👥  Sócios ({len(inv.socios)}):")
        for s in inv.socios:
            cargo = s.get("qualificacao") or "sócio"
            print(f"      - {s['nome']} ({cargo})")

    if inv.candidatos_site and not inv.site:
        print()
        print("  🔗  Candidatos a site (nenhum confirmado):")
        for i, c in enumerate(inv.candidatos_site[:3], 1):
            print(f"      {i}. {c['dominio']} — {c['titulo'][:50]}")

    print("═" * 70)


def pedir_aprovacao(inv: Investigacao) -> bool:
    imprimir_resumo(inv)

    baixas = inv.campos_baixa_confianca(limiar=65)
    if baixas:
        print(f"\n⚠️  Campos com baixa confiança: {', '.join(baixas)}")
        print("   Considere revisar manualmente no Notion antes de aprovar.")

    print()
    while True:
        resp = input("Aprovar e mudar status pra 🔵 Prospect? [s/N]: ").strip().lower()
        if resp in ("s", "sim", "y", "yes"):
            return True
        if resp in ("", "n", "nao", "não", "no"):
            return False
        print("   Resposta inválida. Digite 's' ou 'n'.")


def perguntar_qual_site(inv: Investigacao) -> Optional[str]:

    if not inv.candidatos_site or inv.site:
        return None

    print()
    print("🔎  Encontrei possíveis sites oficiais — qual é o da empresa?")
    for i, c in enumerate(inv.candidatos_site[:5], 1):
        print(f"   [{i}] {c['dominio']}  ({c['titulo'][:60]})")
    print("   [0] Nenhum desses / pular")

    while True:
        resp = input("Escolha (0-5): ").strip()
        if not resp.isdigit():
            print("   Digite um número.")
            continue
        idx = int(resp)
        if idx == 0:
            return None
        if 1 <= idx <= len(inv.candidatos_site):
            return inv.candidatos_site[idx - 1].get("url")
        print(f"   Número fora do intervalo (0-{len(inv.candidatos_site)}).")
