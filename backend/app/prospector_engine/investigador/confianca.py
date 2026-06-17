from dataclasses import dataclass, field

PESOS_FONTE = {
    "usuario": 100,
    "brasilapi": 95,
    "site_oficial": 85,
    "duckduckgo": 60,
    "google_maps": 75,
    "instagram_bio": 70,
    "ia_suposicao": 30,
    "desconhecido": 50,
}


@dataclass
class CampoConfianca:

    valor: str
    fontes: list[str] = field(default_factory=list)

    def score(self) -> int:
        if not self.fontes:
            return 0

        pesos = [PESOS_FONTE.get(f, PESOS_FONTE["desconhecido"]) for f in self.fontes]
        base = max(pesos)

        bonus = min(15, (len(set(self.fontes)) - 1) * 5)

        return min(100, base + bonus)

    def fontes_str(self) -> str:
        return ", ".join(self.fontes) if self.fontes else "(nenhuma)"


@dataclass
class Investigacao:

    nome: CampoConfianca | None = None
    cnpj: CampoConfianca | None = None
    razao_social: CampoConfianca | None = None
    cidade: CampoConfianca | None = None
    estado: CampoConfianca | None = None
    endereco: CampoConfianca | None = None
    site: CampoConfianca | None = None
    instagram: CampoConfianca | None = None
    facebook: CampoConfianca | None = None
    linkedin: CampoConfianca | None = None
    telefone: CampoConfianca | None = None
    whatsapp: CampoConfianca | None = None
    email: CampoConfianca | None = None

    candidatos_site: list[dict] = field(default_factory=list)
    socios: list[dict] = field(default_factory=list)
    capital_social: CampoConfianca | None = None
    cnae_descricao: CampoConfianca | None = None

    def adicionar(self, campo: str, valor: str | None, fonte: str) -> None:

        if valor is None or valor == "":
            return

        valor_str = str(valor).strip()
        if not valor_str:
            return

        atual: CampoConfianca | None = getattr(self, campo, None)

        if atual is None:
            setattr(self, campo, CampoConfianca(valor=valor_str, fontes=[fonte]))
            return

        if atual.valor.lower() == valor_str.lower():
            if fonte not in atual.fontes:
                atual.fontes.append(fonte)
            return

        peso_atual = max(
            PESOS_FONTE.get(f, PESOS_FONTE["desconhecido"]) for f in atual.fontes
        )
        peso_novo = PESOS_FONTE.get(fonte, PESOS_FONTE["desconhecido"])
        if peso_novo > peso_atual:
            setattr(self, campo, CampoConfianca(valor=valor_str, fontes=[fonte]))

    def campos_com_score(self) -> dict[str, tuple]:
        result = {}
        for nome in (
            "nome", "cnpj", "razao_social", "cidade", "estado", "endereco",
            "site", "instagram", "facebook", "linkedin",
            "telefone", "whatsapp", "email",
            "capital_social", "cnae_descricao",
        ):
            campo: CampoConfianca | None = getattr(self, nome, None)
            if campo:
                result[nome] = (campo.valor, campo.score(), campo.fontes_str())
        return result

    def campos_baixa_confianca(self, limiar: int = 70) -> list[str]:
        return [
            nome for nome, (_, score, _) in self.campos_com_score().items()
            if score < limiar
        ]
