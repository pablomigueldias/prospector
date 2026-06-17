from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    fontes: List[str] = field(default_factory=list)

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

    nome: Optional[CampoConfianca] = None
    cnpj: Optional[CampoConfianca] = None
    razao_social: Optional[CampoConfianca] = None
    cidade: Optional[CampoConfianca] = None
    estado: Optional[CampoConfianca] = None
    endereco: Optional[CampoConfianca] = None
    site: Optional[CampoConfianca] = None
    instagram: Optional[CampoConfianca] = None
    facebook: Optional[CampoConfianca] = None
    linkedin: Optional[CampoConfianca] = None
    telefone: Optional[CampoConfianca] = None
    whatsapp: Optional[CampoConfianca] = None
    email: Optional[CampoConfianca] = None

    candidatos_site: List[Dict] = field(default_factory=list)
    socios: List[Dict] = field(default_factory=list)
    capital_social: Optional[CampoConfianca] = None
    cnae_descricao: Optional[CampoConfianca] = None

    def adicionar(self, campo: str, valor: Optional[str], fonte: str) -> None:

        if valor is None or valor == "":
            return

        valor_str = str(valor).strip()
        if not valor_str:
            return

        atual: Optional[CampoConfianca] = getattr(self, campo, None)

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

    def campos_com_score(self) -> Dict[str, tuple]:
        result = {}
        for nome in (
            "nome", "cnpj", "razao_social", "cidade", "estado", "endereco",
            "site", "instagram", "facebook", "linkedin",
            "telefone", "whatsapp", "email",
            "capital_social", "cnae_descricao",
        ):
            campo: Optional[CampoConfianca] = getattr(self, nome, None)
            if campo:
                result[nome] = (campo.valor, campo.score(), campo.fontes_str())
        return result

    def campos_baixa_confianca(self, limiar: int = 70) -> List[str]:
        return [
            nome for nome, (_, score, _) in self.campos_com_score().items()
            if score < limiar
        ]
