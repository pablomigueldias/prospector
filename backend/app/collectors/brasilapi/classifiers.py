from typing import Optional


_CNAE_DIVISAO_TO_SETOR = {
    "05": "Indústria", "06": "Indústria", "07": "Indústria", "08": "Indústria",
    "09": "Indústria",
    "10": "Indústria", "11": "Indústria", "12": "Indústria", "13": "Indústria",
    "14": "Indústria", "15": "Indústria", "16": "Indústria", "17": "Indústria",
    "18": "Indústria", "19": "Indústria", "20": "Indústria", "21": "Indústria",
    "22": "Indústria", "23": "Indústria", "24": "Indústria", "25": "Indústria",
    "26": "Indústria", "27": "Indústria", "28": "Indústria", "29": "Indústria",
    "30": "Indústria", "31": "Indústria", "32": "Indústria", "33": "Indústria",
    "35": "Indústria",
    "36": "Indústria", "37": "Indústria", "38": "Indústria", "39": "Indústria",

    "41": "Imobiliário", "42": "Imobiliário", "43": "Imobiliário",
    "68": "Imobiliário",

    "45": "Varejo",
    "46": "Varejo",
    "47": "Varejo",


    "61": "Tech",
    "62": "Tech",
    "63": "Tech",

    
    "64": "Financeiro",
    "65": "Financeiro",
    "66": "Financeiro",

    
    "69": "Jurídico",

   
    "73": "Marketing",  
    "58": "Marketing",  
    "59": "Marketing",  
    "60": "Marketing",  

    "85": "Educação",

    "86": "Saúde",
    "87": "Saúde",
    "88": "Saúde",

    "49": "Serviços", "50": "Serviços", "51": "Serviços", "52": "Serviços",
    "53": "Serviços", 
    "55": "Serviços", "56": "Serviços",
    "70": "Serviços", "71": "Serviços", "72": "Serviços", 
    "74": "Serviços", "75": "Serviços", 
    "77": "Serviços", 
    "78": "Serviços", 
    "79": "Serviços", 
    "80": "Serviços", "81": "Serviços", "82": "Serviços", 
    "94": "Serviços", "95": "Serviços", "96": "Serviços",
}


def classificar_setor(cnae_codigo: Optional[int]) -> Optional[str]:

    if cnae_codigo is None:
        return None

    cnae_str = str(cnae_codigo).zfill(7)
    divisao = cnae_str[:2]
    return _CNAE_DIVISAO_TO_SETOR.get(divisao)



_LIMITE_PEQUENA = 360_000.0
_LIMITE_MEDIA = 4_800_000.0
_LIMITE_GRANDE = 50_000_000.0


def classificar_tamanho(
    porte_descricao: Optional[str],
    capital_social: Optional[float],
    opcao_mei: bool = False,
) -> Optional[str]:
    
    if opcao_mei:
        return "MEI"

    porte_norm = (porte_descricao or "").upper().strip()

    if "MEI" in porte_norm or "MICROEMPREENDEDOR" in porte_norm:
        return "MEI"
    if porte_norm in ("ME", "MICRO EMPRESA", "MICROEMPRESA"):
        return "Pequena (1-10)"
    if porte_norm in ("EPP", "EMPRESA DE PEQUENO PORTE"):
        return "Média (11-50)"

    if capital_social is None:
        return None

    if capital_social <= _LIMITE_PEQUENA:
        return "Pequena (1-10)"
    if capital_social <= _LIMITE_MEDIA:
        return "Média (11-50)"
    if capital_social <= _LIMITE_GRANDE:
        return "Grande (51-200)"
    return "Corporativa (200+)"
