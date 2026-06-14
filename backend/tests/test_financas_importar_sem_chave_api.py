from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.api.main import app
from tests._financas_auth import usar_usuario
from app.config import settings

IMPORTAR = "/api/financas/importar/boleto"


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — importar boleto sem GEMINI_API_KEY → 400 amigável")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    chave_orig = settings.gemini_api_key
    settings.gemini_api_key = ""  # simula chave ausente
    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            print("\n→ sem chave → 400 com mensagem clara (não 500)")
            r = client.post(
                IMPORTAR,
                files={"file": ("boleto.jpg", b"\xff\xd8\xff\xe0fake", "image/jpeg")},
            )
            assert r.status_code == 400, f"esperava 400, veio {r.status_code}: {r.text}"
            detail = r.json()["detail"].lower()
            assert "gemini_api_key" in detail or "ia" in detail, r.json()
            print(f"   {r.json()['detail']}")
        finally:
            settings.gemini_api_key = chave_orig

    print("\n" + "━" * 60)
    print("TUDO OK — erro amigável de chave ausente!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()
