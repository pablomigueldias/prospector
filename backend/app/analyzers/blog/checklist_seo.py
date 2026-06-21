"""Checklist SEO determinístico do blog (P5 §6.B2) — espelha o checklist
anti-genérico do freela, mas pra SEO on-page.

Puro (sem LLM, sem DB): entra o conteúdo, sai um score 0-100 + itens com
status (ok/warn/fail) e dica. Determinístico = confiável e testável. Cobre o
essencial on-page E o anti-keyword-stuffing (densidade alta vira fail).
"""
from __future__ import annotations

import re
import unicodedata

from app.api.schemas.blog import ChecklistItem, ChecklistSeoResponse

_PESO = {"ok": 1.0, "warn": 0.5, "fail": 0.0}


def _norm(s: str) -> str:
    """minúsculo + sem acento — comparação robusta de keyword."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.casefold()


def _texto_limpo(md: str) -> str:
    """Remove marcação Markdown pra contar palavras de forma honesta."""
    t = re.sub(r"```.*?```", " ", md or "", flags=re.DOTALL)
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[#>*_~`-]", " ", t)
    return t


def _primeiro_paragrafo(md: str) -> str:
    for bloco in re.split(r"\n\s*\n", md or ""):
        b = bloco.strip()
        if b and not b.startswith("#") and not b.startswith("```"):
            return b
    return ""


def avaliar(
    *,
    title: str | None = None,
    slug: str | None = None,
    body_md: str | None = None,
    excerpt: str | None = None,
    meta_description: str | None = None,
    keyword_alvo: str | None = None,
) -> ChecklistSeoResponse:
    itens: list[ChecklistItem] = []

    def add(id_: str, label: str, status: str, dica: str | None = None) -> None:
        itens.append(ChecklistItem(id=id_, label=label, status=status, dica=dica))

    title = title or ""
    body = body_md or ""
    meta = meta_description or ""
    kw = (keyword_alvo or "").strip()
    kw_n = _norm(kw)

    texto = _texto_limpo(body)
    palavras = [p for p in texto.split() if p.strip()]
    n_palavras = len(palavras)
    h2s = re.findall(r"^##\s+(.+)$", body, flags=re.MULTILINE)
    p1 = _primeiro_paragrafo(body)

    # ── Keyword on-page ──────────────────────────────────────────
    if not kw:
        add("keyword", "Keyword-alvo definida", "fail",
            "Defina a keyword-alvo — é o eixo do SEO.")
    else:
        add("keyword", "Keyword-alvo definida", "ok")
        add("kw_title", "Keyword no título", "ok" if kw_n in _norm(title)
            else "fail", "Inclua a keyword no título.")
        add("kw_meta", "Keyword na meta description", "ok" if kw_n in _norm(meta)
            else "warn", "Inclua a keyword na meta description.")
        add("kw_p1", "Keyword no 1º parágrafo", "ok" if kw_n in _norm(p1)
            else "warn", "Use a keyword logo na abertura.")
        add("kw_slug", "Keyword no slug", "ok" if kw_n.replace(" ", "-") in _norm(slug or "")
            else "warn", "Coloque a keyword no slug.")
        add("kw_h2", "Keyword em algum H2", "ok"
            if any(kw_n in _norm(h) for h in h2s) else "warn",
            "Use a keyword em pelo menos um subtítulo.")

        # Anti-keyword-stuffing: densidade da keyword no corpo.
        if n_palavras and kw_n:
            ocorr = _norm(texto).count(kw_n)
            n_tokens_kw = max(1, len(kw_n.split()))
            densidade = (ocorr * n_tokens_kw) / n_palavras
            if densidade > 0.03:
                add("densidade", f"Densidade da keyword ({densidade*100:.1f}%)",
                    "fail", "Keyword stuffing — reduza pra ~0,5-1,5%.")
            elif densidade < 0.003:
                add("densidade", f"Densidade da keyword ({densidade*100:.1f}%)",
                    "warn", "Keyword quase ausente no corpo.")
            else:
                add("densidade", f"Densidade da keyword ({densidade*100:.1f}%)", "ok")

    # ── Tamanhos ─────────────────────────────────────────────────
    tl = len(title)
    add("title_len", f"Título com bom tamanho ({tl} chars)",
        "ok" if 0 < tl <= 60 else "warn",
        "Título ideal ≤ 60 caracteres.")

    ml = len(meta)
    if 120 <= ml <= 160:
        add("meta_len", f"Meta description ({ml} chars)", "ok")
    elif ml == 0:
        add("meta_len", "Meta description ausente", "fail",
            "Escreva uma meta description de 120-160 caracteres.")
    else:
        add("meta_len", f"Meta description ({ml} chars)", "warn",
            "Ideal entre 120 e 160 caracteres.")

    # ── Corpo ────────────────────────────────────────────────────
    add("tamanho", f"Tamanho do texto ({n_palavras} palavras)",
        "ok" if n_palavras >= 600 else "warn" if n_palavras >= 300 else "fail",
        "Mire 600+ palavras pra um artigo que ranqueia.")

    add("headings", f"Subtítulos H2 ({len(h2s)})",
        "ok" if len(h2s) >= 2 else "warn",
        "Use pelo menos 2 seções (##) pra estruturar.")

    tem_link_interno = bool(re.search(r"\]\(/(servicos|blog)", body)) or (
        "reativesystems" in _norm(body)
    )
    add("link_interno", "Link interno (pra /servicos etc.)",
        "ok" if tem_link_interno else "warn",
        "Adicione ao menos 1 link interno (ex.: /servicos/automacao).")

    # Imagens: se houver, exigir alt preenchido.
    imgs = re.findall(r"!\[([^\]]*)\]\([^)]*\)", body)
    if imgs:
        sem_alt = sum(1 for a in imgs if not a.strip())
        add("img_alt", f"Alt nas imagens ({len(imgs)-sem_alt}/{len(imgs)})",
            "ok" if sem_alt == 0 else "warn",
            "Toda imagem precisa de texto alternativo (alt).")

    add("excerpt", "Resumo (excerpt) preenchido",
        "ok" if (excerpt or "").strip() else "warn",
        "Um bom resumo melhora o CTR no Google e nos cards.")

    # ── Score ────────────────────────────────────────────────────
    total = sum(_PESO[i.status] for i in itens)
    score = round(100 * total / len(itens)) if itens else 0
    nivel = (
        "otimo" if score >= 90 else
        "bom" if score >= 75 else
        "ok" if score >= 50 else
        "ruim"
    )
    return ChecklistSeoResponse(score=score, nivel=nivel, itens=itens)
