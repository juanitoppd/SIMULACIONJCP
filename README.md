# Simulación TechClassUC — Interfaz web

Permite ejecutar la simulación desde un formulario web, ver y descargar resultados.

Requisitos
- Python 3.10+
- Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar la app localmente

```bash
python app.py
# abrir http://localhost:5000
```

Uso
- Ingresa los parámetros en la página y presiona *Ejecutar simulación*.
- La simulación se ejecuta en segundo plano. La página muestra el estado y refresca las imágenes cuando termina.
- Descarga las métricas en formato JSON o CSV desde los enlaces en la sección *Resultados*.

Archivos importantes
- `app.py`: servidor Flask y lógica de ejecución.
- `main.py`: versión CLI de la simulación.
- `templates/index.html`: plantilla web.
- `static/style.css`: estilos.
- `resultados/`: carpeta donde se guardan PNG y `last_metrics.json`.
# SIMUALACION — TechClassUC (M/M/c)

Proyecto de simulación M/M/c usando SimPy y Monte Carlo.

## Ejecutar localmente

Instala dependencias:

```bash
python -m pip install -r requirements.txt
```

Generar resultados (30 réplicas):

```bash
python main.py --n 30 --output resultados
```

Levantar la API local (ver imágenes en `resultados`):

```bash
python app.py
# o con gunicorn (Linux):
# gunicorn app:app --bind 0.0.0.0:8000
```

## Despliegue en Render

Recomendado: crear un **Web Service** con estos valores:

- Root Directory: (vacío)
- Build Command:

```bash
pip install -r requirements.txt
```

- Start Command:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

Notas:
- Asegúrate de que `requirements.txt` incluya `flask` y `gunicorn` (ya están añadidos).
- Render instala paquetes en un entorno Linux; `gunicorn` no funciona como comando en Windows, pero en Render sí.
- Si prefieres que Render ejecute la simulación como job en segundo plano, crea un **Worker** y usa `python main.py --n 30 --output resultados` como Start Command.

## Solución de problemas

- Si el log de deploy muestra `Exited with status 127`, revisa si el Start Command existe en el entorno (por ejemplo `gunicorn` debe instalarse desde `requirements.txt`).
- Revisa los logs completos en Render para identificar el paso que falla (Build vs Start).

---
