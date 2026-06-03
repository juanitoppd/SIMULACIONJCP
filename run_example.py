"""Ejecuta una simulación de prueba rápida para verificar que la UI y generación de resultados funcionan."""
from app import run_simulation

params = {
    'lmbda': 10.0,
    'mu': 6.0,
    'c': 2,
    't_sim': 120.0,
    't_warm': 20.0,
    'n': 3,
}

if __name__ == '__main__':
    resumen = run_simulation(params, output_dir='resultados')
    print('Resumen generado. Revisa la carpeta resultados/ y el archivo resultados/last_metrics.json')
