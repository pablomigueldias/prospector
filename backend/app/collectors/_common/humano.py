import random
import time


def delay_humano_curto() -> float:
    return min(15.0, max(0.2, random.lognormvariate(0.4, 0.7)))


def delay_humano_medio() -> float:
    return min(45.0, max(0.5, random.lognormvariate(1.4, 0.6)))


def delay_humano_longo() -> float:
    return min(180.0, max(2.0, random.lognormvariate(2.7, 0.7)))


def esperar_curto() -> float:
    d = delay_humano_curto()
    time.sleep(d)
    return d


def esperar_medio() -> float:
    d = delay_humano_medio()
    time.sleep(d)
    return d


def esperar_longo() -> float:
    d = delay_humano_longo()
    time.sleep(d)
    return d


def jitter(valor: float, percentual: float = 0.25) -> float:
    delta = valor * percentual
    return valor + random.uniform(-delta, delta)



def aquecer_sessao(min_segundos: float = 60.0, max_segundos: float = 180.0) -> None:
    d = random.uniform(min_segundos, max_segundos)
    time.sleep(d)

class PadraoHumano:
    def __init__(self):
        self.acoes_na_rajada = 0
        self.max_rajada = random.randint(3, 6)

    def proximo_delay(self) -> float:
        self.acoes_na_rajada += 1
        if self.acoes_na_rajada >= self.max_rajada:
            self.acoes_na_rajada = 0
            self.max_rajada = random.randint(3, 6)
            return delay_humano_longo()
        else:
            return delay_humano_medio()

    def esperar(self) -> float:
        d = self.proximo_delay()
        time.sleep(d)
        return d
