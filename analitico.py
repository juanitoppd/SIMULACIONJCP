import math
from typing import Dict


def mmc_rho(lmbda: float, mu: float, c: int) -> float:
    return lmbda / (c * mu)


def mmc_p0(lmbda: float, mu: float, c: int) -> float:
    rho = mmc_rho(lmbda, mu, c)
    if rho >= 1.0:
        raise ValueError("Sistema inestable: rho >= 1")

    suma = sum((lmbda / mu) ** k / math.factorial(k) for k in range(c))
    termino_c = (lmbda / mu) ** c / math.factorial(c)
    p0 = 1.0 / (suma + termino_c * (c * mu) / (c * mu - lmbda))
    return p0


def mmc_lq(lmbda: float, mu: float, c: int) -> float:
    rho = mmc_rho(lmbda, mu, c)
    p0 = mmc_p0(lmbda, mu, c)
    término_c = (lmbda / mu) ** c / math.factorial(c)
    lq = p0 * término_c * rho / ((1.0 - rho) ** 2)
    return lq


def mmc_wq(lmbda: float, mu: float, c: int) -> float:
    lq = mmc_lq(lmbda, mu, c)
    return lq / lmbda


def mmc_l(lmbda: float, mu: float, c: int) -> float:
    return mmc_lq(lmbda, mu, c) + lmbda / mu


def mmc_w(lmbda: float, mu: float, c: int) -> float:
    return mmc_wq(lmbda, mu, c) + 1.0 / mu


def comparar_con_simulacion(sim_metrics: Dict[str, float], lmbda: float, mu: float, c: int) -> Dict[str, float]:
    analitico = {
        "rho": mmc_rho(lmbda, mu, c),
        "Lq": mmc_lq(lmbda, mu, c),
        "Wq": mmc_wq(lmbda, mu, c),
        "L": mmc_l(lmbda, mu, c),
        "W": mmc_w(lmbda, mu, c),
    }
    comparacion = {}
    for clave, valor in analitico.items():
        sim_val = sim_metrics.get(clave if clave != "W" else "Ws_promedio", sim_metrics.get(clave, 0.0))
        comparacion[clave] = {
            "analitico": valor,
            "simulacion": sim_val,
            "error_relativo_pct": abs((sim_val - valor) / valor) * 100.0 if valor else 0.0,
        }
    return comparacion
