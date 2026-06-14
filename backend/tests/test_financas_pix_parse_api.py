from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi.testclient import TestClient

from app.api.main import app
from tests._financas_auth import usar_usuario

PARSE = "/api/financas/pix/parse"


def _tlv(tag: str, val: str) -> str:
    return f"{tag}{len(val):02d}{val}"


def _montar_pix(valor: str | None, nome: str, cidade: str, chave: str) -> str:
    mai = _tlv("00", "br.gov.bcb.pix") + _tlv("01", chave)
    campos = [
        _tlv("00", "01"),
        _tlv("26", mai),
        _tlv("52", "0000"),
        _tlv("53", "986"),
    ]
    if valor is not None:
        campos.append(_tlv("54", valor))
    campos += [
        _tlv("58", "BR"),
        _tlv("59", nome),
        _tlv("60", cidade),
        _tlv("63", "ABCD"),  # CRC dummy (parser não valida)
    ]
    return "".join(campos)


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — PIX copia-e-cola (parser)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    with TestClient(app) as client:
        usar_usuario(usuario_id)

        print("\n→ Test 1: PIX com valor → extrai tudo")
        codigo = _montar_pix("30.00", "Pablo Dias", "SAO PAULO", "pablo@gmail.com")
        r = client.post(PARSE, json={"codigo": codigo})
        assert r.status_code == 200, r.text
        b = r.json()
        assert Decimal(b["valor"]) == Decimal("30.00"), b
        assert b["beneficiario"] == "Pablo Dias", b
        assert b["cidade"] == "SAO PAULO", b
        assert b["chave"] == "pablo@gmail.com", b
        print(f"   {b}")

        print("\n→ Test 2: PIX sem valor (cobrança aberta) → valor nulo")
        codigo = _montar_pix(None, "Loja X", "RIO", "11999998888")
        b = client.post(PARSE, json={"codigo": codigo}).json()
        assert b["valor"] is None and b["beneficiario"] == "Loja X", b
        print(f"   {b}")

        print("\n→ Test 3: com espaços/quebras → ainda lê")
        codigo = _montar_pix("12.50", "Maria", "BH", "chave-x")
        b = client.post(PARSE, json={"codigo": f"  {codigo[:20]}\n{codigo[20:]} "}).json()
        assert Decimal(b["valor"]) == Decimal("12.50"), b
        print(f"   valor={b['valor']}")

        print("\n→ Test 4: lixo → 400")
        r = client.post(PARSE, json={"codigo": "isto não é um pix"})
        assert r.status_code == 400, r.status_code
        print(f"   barrou: {r.json()['detail']}")

    print("\n" + "━" * 60)
    print("TUDO OK — parser de PIX funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()
