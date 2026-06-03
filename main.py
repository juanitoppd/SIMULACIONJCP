import argparse
import math
import os

from analitico import comparar_con_simulacion, mmc_rho
from montecarlo import correr_replicas
from sensibilidad import barrido_sensibilidad
from simulacion_des import correr_una_replica
from visualizacion import (
    plot_distribucion_medias,
    plot_evolucion_temporal,
    plot_histograma_wq,
    plot_rho_vs_lambda,
    plot_wq_vs_c,
)


def imprimir_reporte(estadisticas: dict, comparacion: dict) -> None:
    print("\n===== RESULTADOS DE SIMULACIÓN =====")
    print(f"Wq promedio (min): {estadisticas['Wq_promedio']:.4f}")
    print(f"Ws promedio (min): {estadisticas['Ws_promedio']:.4f}")
    print(f"Lq promedio: {estadisticas['Lq_promedio']:.4f}")
    print(f"Utilización promedio ρ: {estadisticas['rho_promedio']:.4f}")
    print(f"Intervalo de confianza 95% Wq: ±{estadisticas['intervalo_Wq_95']:.4f} min")
    print(f"Réplicas necesarias para error ≤5%: {estadisticas['min_replicas_5pct']}")
    print("\n===== COMPARACIÓN ANALÍTICA M/M/c =====")
    for clave, valores in comparacion.items():
        print(f"{clave}: analítico={valores['analitico']:.4f}, sim={valores['simulacion']:.4f}, error_relativo={valores['error_relativo_pct']:.2f}%")


def construir_caracteristicas_sensibilidad(resultados: list) -> tuple:
    c_values = sorted({item['c'] for item in resultados})
    lambda_values = sorted({item['lambda'] for item in resultados})
    rho_by_c = []
    wq_means_by_c = []
    for c in c_values:
        rho_row = []
        wq_row = []
        for lmbda in lambda_values:
            fila = next((item for item in resultados if item['c'] == c and item['lambda'] == lmbda), None)
            rho_row.append(float(fila['rho']) if fila and fila['rho'] is not None else float('nan'))
            wq_row.append(float(fila['Wq_promedio']) if fila and fila['Wq_promedio'] is not None else float('nan'))
        rho_by_c.append(rho_row)
        wq_means_by_c.append(wq_row)
    return c_values, lambda_values, rho_by_c, wq_means_by_c


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulación M/M/c con SimPy y Monte Carlo")
    parser.add_argument("--lambda", dest="lmbda", type=float, default=10.0, help="Tasa de llegada (clientes/hora)")
    parser.add_argument("--mu", type=float, default=4.0, help="Tasa de servicio por servidor (clientes/hora)")
    parser.add_argument("--c", type=int, default=3, help="Número de servidores")
    parser.add_argument("--t_sim", type=float, default=480.0, help="Duración de la simulación en minutos")
    parser.add_argument("--t_warm", type=float, default=60.0, help="Período de calentamiento en minutos")
    parser.add_argument("--n", type=int, default=30, help="Número de réplicas de Monte Carlo")
    parser.add_argument("--output", type=str, default="output", help="Carpeta de salida para gráficos")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    rho = mmc_rho(args.lmbda, args.mu, args.c)
    if rho >= 1.0:
        raise SystemExit(f"Sistema inestable con ρ = {rho:.4f}. Ajuste λ, μ o c para que ρ < 1.")

    estadisticas = correr_replicas(args.n, args.lmbda, args.mu, args.c, args.t_sim, args.t_warm)
    comparacion = comparar_con_simulacion({
        "Wq": estadisticas["Wq_promedio"] / 60.0 if estadisticas["Wq_promedio"] else 0.0,
        "Ws_promedio": estadisticas["Ws_promedio"] / 60.0 if estadisticas["Ws_promedio"] else 0.0,
        "Lq": estadisticas["Lq_promedio"],
        "L": estadisticas["Lq_promedio"] + args.lmbda / args.mu,
        "rho": estadisticas["rho_promedio"],
    }, args.lmbda, args.mu, args.c)

    imprimir_reporte(estadisticas, comparacion)

    # Gráficas principales
    replica_representativa = correr_una_replica(args.lmbda, args.mu, args.c, args.t_sim, args.t_warm, seed=999, return_trace=True)
    plot_evolucion_temporal(replica_representativa["times"], replica_representativa["n_system_trace"], os.path.join(args.output, "evolucion_temporal.png"))
    plot_histograma_wq(replica_representativa["wq_values"], os.path.join(args.output, "histograma_wq.png"))
    plot_distribucion_medias([r["Wq_promedio"] for r in estadisticas["replicas"]], os.path.join(args.output, "distribucion_medias_wq.png"))

    # Sensibilidad
    c_grid = [max(1, args.c - 2), args.c - 1, args.c, args.c + 1, args.c + 2]
    c_grid = [c for c in sorted(set(c_grid)) if c > 0]
    lambda_grid = [args.lmbda * f for f in [0.8, 1.0, 1.2, 1.4]]
    sensibilidad = barrido_sensibilidad(c_grid, lambda_grid, args.mu, args.t_sim, args.t_warm, n_replicas=10)

    c_values, lambda_values, rho_by_c, wq_means_by_c = construir_caracteristicas_sensibilidad(sensibilidad["resultados"])
    if c_values and lambda_values:
        wq_promedios_por_c = []
        for wq_row in wq_means_by_c:
            valores_validos = [valor for valor in wq_row if not math.isnan(valor)]
            wq_promedios_por_c.append(sum(valores_validos) / len(valores_validos) if valores_validos else float('nan'))

        plot_wq_vs_c(c_values, wq_promedios_por_c, os.path.join(args.output, "wq_vs_c.png"))
        plot_rho_vs_lambda(lambda_values, rho_by_c, c_values, os.path.join(args.output, "rho_vs_lambda.png"))

    print(f"\nSe han generado gráficos en: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
