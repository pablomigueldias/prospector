from __future__ import annotations

import time

from app.api.services.auth import senha_service as ss


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step 2 (Argon2id + força de senha)")
    print("━" * 60)

    # ── 1. Hash + verify ─────────────────────────────────────────────
    print("\n→ Test 1: hash e confere")
    senha = "umaSenhaForte-2026!"
    h = ss.hash_senha(senha)
    assert h.startswith("$argon2id$"), h[:20]
    assert ss.conferir_senha(h, senha) is True
    assert ss.conferir_senha(h, "senha errada qualquer") is False
    print(f"   hash ok ({h[:24]}...), confere certo/errado")

    # ── 2. Hashes diferentes pra mesma senha (salt) ──────────────────
    print("\n→ Test 2: salt → hashes distintos")
    assert ss.hash_senha(senha) != ss.hash_senha(senha)
    print("   dois hashes da mesma senha são diferentes ✓")

    # ── 3. Anti-timing: hash None gasta tempo e retorna False ────────
    print("\n→ Test 3: anti-timing (usuário inexistente)")
    t0 = time.perf_counter()
    assert ss.conferir_senha(None, senha) is False
    dt_none = time.perf_counter() - t0
    t0 = time.perf_counter()
    ss.conferir_senha(h, "errada")
    dt_real = time.perf_counter() - t0
    # Os dois caminhos rodam um verify Argon2 → tempos na mesma ordem de grandeza.
    assert dt_none > 0.005, dt_none
    print(f"   none={dt_none*1000:.0f}ms real={dt_real*1000:.0f}ms (ambos gastam CPU)")

    # ── 4. Força de senha ────────────────────────────────────────────
    print("\n→ Test 4: validação de força")
    ss.validar_forca("umaSenhaBoa-123")  # ok, não levanta
    for ruim, motivo in [
        ("curta1", "curta"),
        ("123456789012", "só números"),
        ("password", "comum"),
        ("aaaaaaaaaaaa", "repetição"),
    ]:
        try:
            ss.validar_forca(ruim)
            assert False, f"deveria ter barrado: {ruim!r} ({motivo})"
        except ss.SenhaFraca:
            pass
    print("   aceita boa; barra curta/numérica/comum/repetida ✓")

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step 2 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()
