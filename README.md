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
