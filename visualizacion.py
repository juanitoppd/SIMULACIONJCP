from typing import List, Sequence

import matplotlib.pyplot as plt


def plot_evolucion_temporal(times: Sequence[float],
                             n_system: Sequence[int],
                             filename: str) -> None:
    plt.figure(figsize=(10, 5))
    plt.step(times, n_system, where="post")
    plt.title("Evolución temporal del número de clientes en el sistema")
    plt.xlabel("Tiempo (minutos)")
    plt.ylabel("Clientes en el sistema")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.savefig(filename, dpi=200)
    plt.close()


def plot_histograma_wq(wq_values: Sequence[float], filename: str) -> None:
    plt.figure(figsize=(8, 5))
    plt.hist(wq_values, bins=20, color="#4C72B0", edgecolor="black")
    plt.title("Histograma de tiempos de espera en cola Wq")
    plt.xlabel("Tiempo de espera Wq (minutos)")
    plt.ylabel("Frecuencia")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.savefig(filename, dpi=200)
    plt.close()


def plot_wq_vs_c(c_values: Sequence[int],
                 wq_means: Sequence[float],
                 filename: str) -> None:
    plt.figure(figsize=(8, 5))
    plt.plot(c_values, wq_means, marker="o", linestyle="-", color="#DD8452")
    plt.title("Tiempo promedio de espera Wq vs. número de servidores c")
    plt.xlabel("Número de servidores c")
    plt.ylabel("Wq promedio (minutos)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.savefig(filename, dpi=200)
    plt.close()


def plot_rho_vs_lambda(lambda_values: Sequence[float],
                       rho_by_c: List[Sequence[float]],
                       c_values: Sequence[int],
                       filename: str) -> None:
    plt.figure(figsize=(8, 5))
    for c, rho_values in zip(c_values, rho_by_c):
        plt.plot(lambda_values, rho_values, marker="o", label=f"c={c}")
    plt.title("Utilización ρ vs. tasa de llegada λ")
    plt.xlabel("Tasa de llegada λ (clientes/hora)")
    plt.ylabel("Utilización ρ")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.savefig(filename, dpi=200)
    plt.close()


def plot_distribucion_medias(wq_means: Sequence[float], filename: str) -> None:
    plt.figure(figsize=(8, 5))
    plt.hist(wq_means, bins=15, color="#55A868", edgecolor="black")
    plt.title("Distribución de las medias de Wq entre réplicas")
    plt.xlabel("Wq promedio (minutos)")
    plt.ylabel("Frecuencia")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.savefig(filename, dpi=200)
    plt.close()
