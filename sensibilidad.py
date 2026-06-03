from typing import Dict, List

from montecarlo import correr_replicas


def barrido_sensibilidad(c_values: List[int],
                        lambda_values: List[float],
                        mu: float,
                        t_sim: float,
                        t_warm: float,
                        n_replicas: int = 20,
                        seed_base: int = 100) -> Dict[str, List[Dict[str, object]]]:
    resultados = []
    for c in c_values:
        for lmbda in lambda_values:
            if lmbda / (c * mu) >= 1.0:
                resultados.append({
                    "c": c,
                    "lambda": lmbda,
                    "rho": lmbda / (c * mu),
                    "Wq_promedio": None,
                    "Lq_promedio": None,
                    "nota": "inestable",
                })
                continue

            datos = correr_replicas(n_replicas, lmbda, mu, c, t_sim, t_warm, seed_base=seed_base + c * 100 + int(lmbda * 10))
            resultados.append({
                "c": c,
                "lambda": lmbda,
                "rho": datos["rho_promedio"],
                "Wq_promedio": datos["Wq_promedio"],
                "Lq_promedio": datos["Lq_promedio"],
                "nota": "estable",
            })
    return {"resultados": resultados}
