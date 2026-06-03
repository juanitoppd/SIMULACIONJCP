import math
import statistics
from typing import Dict, List, Optional

from simulacion_des import correr_una_replica


def intervalo_confianza(promedio: float, desviacion: float, n: int, nivel: float = 0.95) -> float:
    if n <= 1 or desviacion == 0.0:
        return 0.0
    z = 1.96 if nivel == 0.95 else 1.96
    return z * desviacion / math.sqrt(n)


def replicas_minimas(promedio: float, desviacion: float, error_relativo: float = 0.05) -> int:
    if promedio == 0.0 or desviacion == 0.0:
        return 1
    factor = 1.96 * desviacion / (error_relativo * promedio)
    return max(1, math.ceil(factor ** 2))


def correr_replicas(n: int,
                    lmbda: float,
                    mu: float,
                    c: int,
                    t_sim: float,
                    t_warm: float,
                    seed_base: int = 42) -> Dict[str, object]:
    resultados: List[Dict[str, float]] = []
    for i in range(n):
        replica = correr_una_replica(lmbda, mu, c, t_sim, t_warm, seed=seed_base + i)
        resultados.append(replica)

    wq_promedios = [r["Wq_promedio"] for r in resultados]
    ws_promedios = [r["Ws_promedio"] for r in resultados]
    lq_promedios = [r["Lq_promedio"] for r in resultados]
    rho_promedios = [r["rho"] for r in resultados]

    estadisticas = {
        "Wq_promedio": statistics.mean(wq_promedios) if wq_promedios else 0.0,
        "Ws_promedio": statistics.mean(ws_promedios) if ws_promedios else 0.0,
        "Lq_promedio": statistics.mean(lq_promedios) if lq_promedios else 0.0,
        "rho_promedio": statistics.mean(rho_promedios) if rho_promedios else 0.0,
        "Wq_std": statistics.stdev(wq_promedios) if len(wq_promedios) > 1 else 0.0,
        "Ws_std": statistics.stdev(ws_promedios) if len(ws_promedios) > 1 else 0.0,
        "Lq_std": statistics.stdev(lq_promedios) if len(lq_promedios) > 1 else 0.0,
        "rho_std": statistics.stdev(rho_promedios) if len(rho_promedios) > 1 else 0.0,
        "N_replicas": n,
        "intervalo_Wq_95": intervalo_confianza(statistics.mean(wq_promedios), statistics.stdev(wq_promedios) if len(wq_promedios) > 1 else 0.0, len(wq_promedios)),
        "intervalo_Ws_95": intervalo_confianza(statistics.mean(ws_promedios), statistics.stdev(ws_promedios) if len(ws_promedios) > 1 else 0.0, len(ws_promedios)),
        "intervalo_Lq_95": intervalo_confianza(statistics.mean(lq_promedios), statistics.stdev(lq_promedios) if len(lq_promedios) > 1 else 0.0, len(lq_promedios)),
        "intervalo_rho_95": intervalo_confianza(statistics.mean(rho_promedios), statistics.stdev(rho_promedios) if len(rho_promedios) > 1 else 0.0, len(rho_promedios)),
        "min_replicas_5pct": replicas_minimas(statistics.mean(wq_promedios), statistics.stdev(wq_promedios) if len(wq_promedios) > 1 else 0.0),
        "replicas": resultados,
    }
    return estadisticas
