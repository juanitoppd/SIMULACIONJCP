import os
import json
import threading
import time
import csv
import io
from flask import (
    Flask,
    send_from_directory,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    Response,
)
import zipfile
import tempfile

# Forzar backend no interactivo para matplotlib (evitar errores en servidores sin DISPLAY)
try:
    import matplotlib
    matplotlib.use('Agg')
except Exception:
    pass

from analitico import mmc_rho
from montecarlo import correr_replicas
from simulacion_des import correr_una_replica
from visualizacion import (
    plot_distribucion_medias,
    plot_evolucion_temporal,
    plot_histograma_wq,
    plot_rho_vs_lambda,
    plot_wq_vs_c,
)

 # Servir archivos estáticos desde la carpeta `static` (CSS, imágenes, favicon)
app = Flask(__name__, static_folder='static', static_url_path='/static', template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET', 'dev_secret')


def run_simulation(params: dict, output_dir: str = 'resultados') -> dict:
    os.makedirs(output_dir, exist_ok=True)

    lmbda = float(params.get('lmbda', 10.0))
    mu = float(params.get('mu', 4.0))
    c = int(params.get('c', 3))
    t_sim = float(params.get('t_sim', 480.0))
    t_warm = float(params.get('t_warm', 60.0))
    n = int(params.get('n', 30))

    rho = mmc_rho(lmbda, mu, c)
    if rho >= 1.0:
        raise ValueError(f"Sistema inestable con ρ = {rho:.4f}. Ajuste λ, μ o c para que ρ < 1.")

    estadisticas = correr_replicas(n, lmbda, mu, c, t_sim, t_warm)

    # Gráficas principales (proteger con try/except para fallback)
    replica_representativa = correr_una_replica(lmbda, mu, c, t_sim, t_warm, seed=999, return_trace=True)
    try:
        plot_evolucion_temporal(replica_representativa['times'], replica_representativa['n_system_trace'], os.path.join(output_dir, 'evolucion_temporal.png'))
        plot_histograma_wq(replica_representativa['wq_values'], os.path.join(output_dir, 'histograma_wq.png'))
        plot_distribucion_medias([r['Wq_promedio'] for r in estadisticas['replicas']], os.path.join(output_dir, 'distribucion_medias_wq.png'))
    except Exception as e:
        # crear placeholders PNG simples si falla la generación de gráficas
        try:
            from PIL import Image, ImageDraw, ImageFont
            def make_placeholder(path, text='placeholder'):
                img = Image.new('RGB', (640, 360), color=(245, 249, 255))
                d = ImageDraw.Draw(img)
                try:
                    f = ImageFont.load_default()
                except Exception:
                    f = None
                w, h = d.textsize(text, font=f)
                d.text(((640-w)/2, (360-h)/2), text, fill=(130,160,190), font=f)
                img.save(path)

            make_placeholder(os.path.join(output_dir, 'evolucion_temporal.png'), 'evolucion')
            make_placeholder(os.path.join(output_dir, 'histograma_wq.png'), 'histograma')
            make_placeholder(os.path.join(output_dir, 'distribucion_medias_wq.png'), 'distribucion')
        except Exception:
            # si PIL no está disponible, copiar el placeholder SVG convertido no trivial; en su lugar, crear archivos vacíos
            for fname in ('evolucion_temporal.png','histograma_wq.png','distribucion_medias_wq.png'):
                open(os.path.join(output_dir, fname), 'a').close()

    # Sensibilidad (pequeño barrido)
    c_grid = [max(1, c - 2), c - 1, c, c + 1, c + 2]
    c_grid = [ci for ci in sorted(set(c_grid)) if ci > 0]
    lambda_grid = [lmbda * f for f in [0.8, 1.0, 1.2, 1.4]]
    from sensibilidad import barrido_sensibilidad

    sensibilidad = barrido_sensibilidad(c_grid, lambda_grid, mu, t_sim, t_warm, n_replicas=6)
    # preparar datos para graficar rho vs lambda
    c_values = sorted({item['c'] for item in sensibilidad['resultados']})
    lambda_values = sorted({item['lambda'] for item in sensibilidad['resultados']})
    rho_by_c = []
    wq_means_by_c = []
    for ci in c_values:
        rho_row = []
        wq_row = []
        for lmb in lambda_values:
            fila = next((it for it in sensibilidad['resultados'] if it['c'] == ci and it['lambda'] == lmb), None)
            rho_row.append(float(fila['rho']) if fila and fila['rho'] is not None else float('nan'))
            wq_row.append(float(fila['Wq_promedio']) if fila and fila['Wq_promedio'] is not None else float('nan'))
        rho_by_c.append(rho_row)
        wq_means_by_c.append(wq_row)

    if c_values and lambda_values:
        wq_promedios_por_c = []
        for wq_row in wq_means_by_c:
            valores_validos = [v for v in wq_row if not (v != v)]  # remove nan
            wq_promedios_por_c.append(sum(valores_validos) / len(valores_validos) if valores_validos else float('nan'))
        plot_wq_vs_c(c_values, wq_promedios_por_c, os.path.join(output_dir, 'wq_vs_c.png'))
        plot_rho_vs_lambda(lambda_values, rho_by_c, c_values, os.path.join(output_dir, 'rho_vs_lambda.png'))

    # Guardar métricas resumen
    resumen = {
        'params': {'lmbda': lmbda, 'mu': mu, 'c': c, 't_sim': t_sim, 't_warm': t_warm, 'n': n},
        'estadisticas': estadisticas,
        'sensibilidad': sensibilidad,
    }
    with open(os.path.join(output_dir, 'last_metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(resumen, f, default=str, indent=2)

    return resumen


def write_status(status: dict, output_dir: str = 'resultados') -> None:
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'status.json'), 'w', encoding='utf-8') as f:
        json.dump(status, f, default=str)


def background_worker(params: dict, output_dir: str = 'resultados') -> None:
    try:
        write_status({'phase': 'started', 'message': 'Iniciando simulación', 'progress': 0}, output_dir)
        # validate rho early
        rho = mmc_rho(float(params.get('lmbda', 10.0)), float(params.get('mu', 4.0)), int(params.get('c', 3)))
        if rho >= 1.0:
            write_status({'phase': 'error', 'message': f'Sistema inestable con ρ = {rho:.4f}'}, output_dir)
            return

        write_status({'phase': 'running', 'message': 'Ejecutando réplicas Monte Carlo', 'progress': 20}, output_dir)
        # run simulation (this may take time)
        resumen = run_simulation(params, output_dir=output_dir)

        write_status({'phase': 'postprocessing', 'message': 'Generando gráficos y resultados', 'progress': 90}, output_dir)
        # small sleep to ensure files are flushed
        time.sleep(0.5)
        write_status({'phase': 'done', 'message': 'Simulación completada', 'progress': 100}, output_dir)
    except Exception as e:
        write_status({'phase': 'error', 'message': str(e)}, output_dir)


def process_bulk_items(items: list, output_dir: str = 'resultados') -> str:
    """Process a list of parameter dicts, save per-case results and return path to ZIP file."""
    os.makedirs(output_dir, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix='batch_')
    files_to_zip = []
    for idx, params in enumerate(items, start=1):
        prefix = f'case_{idx}_'
        write_status({'phase': 'running_batch', 'message': f'Procesando caso {idx}/{len(items)}', 'progress': int(100*idx/len(items))}, output_dir)
        try:
            resumen = run_simulation(params, output_dir=output_dir)
            # save resumen per case
            case_json = os.path.join(tmpdir, f'{prefix}metrics.json')
            with open(case_json, 'w', encoding='utf-8') as f:
                json.dump(resumen, f, indent=2, default=str)
            files_to_zip.append(case_json)
            # copy generated images for this run (they use fixed names) and rename with prefix
            for fname in ('evolucion_temporal.png','histograma_wq.png','distribucion_medias_wq.png','wq_vs_c.png','rho_vs_lambda.png'):
                src = os.path.join(output_dir, fname)
                if os.path.exists(src):
                    dest = os.path.join(tmpdir, prefix + fname)
                    try:
                        from shutil import copy2
                        copy2(src, dest)
                        files_to_zip.append(dest)
                    except Exception:
                        pass
        except Exception as e:
            errfile = os.path.join(tmpdir, f'{prefix}error.txt')
            with open(errfile, 'w', encoding='utf-8') as f:
                f.write(str(e))
            files_to_zip.append(errfile)

    # create zip
    zip_path = os.path.join(output_dir, 'batch_results.zip')
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files_to_zip:
            arcname = os.path.basename(path)
            zf.write(path, arcname=arcname)

    write_status({'phase': 'done_batch', 'message': 'Batch completado', 'zip': zip_path}, output_dir)
    return zip_path


def parse_batch_text(text: str) -> list:
    text = text.strip()
    if not text:
        return []

    if text[0] in '[{':
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
        raise ValueError('JSON debe ser una lista o un objeto.')

    reader = csv.DictReader(text.splitlines())
    items = []
    for row in reader:
        if not any(row.values()):
            continue
        params = {}
        for key, value in row.items():
            if value is None:
                continue
            value = value.strip()
            if value == '':
                continue
            try:
                num = float(value)
                if num.is_integer():
                    value = int(num)
                else:
                    value = num
            except ValueError:
                pass
            params[key] = value
        for key in ('c', 'n'):
            if key in params:
                try:
                    params[key] = int(float(params[key]))
                except Exception:
                    pass
        if params:
            items.append(params)
    return items


@app.route('/upload', methods=['POST'])
def upload():
    bulk_text = request.form.get('bulk_text', '').strip()
    file = request.files.get('file')
    items = []
    try:
        if file and file.filename:
            content = file.read().decode('utf-8')
            try:
                items = parse_batch_text(content)
            except json.JSONDecodeError:
                flash('Archivo subido no es JSON o CSV válido.', 'danger')
                return redirect(url_for('index'))
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('index'))
        elif bulk_text:
            try:
                items = parse_batch_text(bulk_text)
            except json.JSONDecodeError:
                flash('Texto no es JSON o CSV válido. Usa CSV o JSON para lote.', 'danger')
                return redirect(url_for('index'))
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('index'))

        if not items:
            flash('No se encontraron parámetros para procesar en el lote.', 'danger')
            return redirect(url_for('index'))

        thread = threading.Thread(target=process_bulk_items, args=(items, 'resultados'), daemon=True)
        thread.start()
        flash(f'Lote iniciado ({len(items)} casos). Se generará resultados/batch_results.zip', 'success')
    except Exception as e:
        flash(f'Error al procesar lote: {e}', 'danger')

    return redirect(url_for('index'))


@app.route('/download_batch')
def download_batch():
    path = os.path.join('resultados','batch_results.zip')
    if os.path.exists(path):
        return send_from_directory('resultados','batch_results.zip', as_attachment=True)
    return Response('No batch results', status=404)



@app.route('/')
def index():
    resultados_dir = os.path.abspath('resultados')
    archivos = []
    if os.path.isdir(resultados_dir):
        archivos = sorted([f for f in os.listdir(resultados_dir) if any(f.endswith(ext) for ext in ('.png', '.jpg', '.jpeg'))])

    metrics = None
    metrics_path = os.path.join('resultados', 'last_metrics.json')
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
        except Exception:
            metrics = None

    return render_template('index.html', images=archivos, metrics=metrics)


@app.route('/run', methods=['POST'])
def run():
    try:
        params = {
            'lmbda': request.form.get('lmbda', type=float),
            'mu': request.form.get('mu', type=float),
            'c': request.form.get('c', type=int),
            't_sim': request.form.get('t_sim', type=float),
            't_warm': request.form.get('t_warm', type=float),
            'n': request.form.get('n', type=int),
        }
        # start background thread so the request returns quickly
        thread = threading.Thread(target=background_worker, args=(params, 'resultados'), daemon=True)
        thread.start()
        flash('Simulación iniciada en segundo plano. Revisa el estado en la página.', 'success')
    except Exception as e:
        flash(f'Error al ejecutar simulación: {e}', 'danger')
    # soportar XHR: si petición fetch, devolver JSON, si no, redirect
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'started'})
    return redirect(url_for('index'))


@app.route('/demo', methods=['POST', 'GET'])
def demo():
    """Ejecuta una simulación rápida de demo para generar gráficas de ejemplo."""
    params = {'lmbda': 10.0, 'mu': 4.0, 'c': 3, 't_sim': 60.0, 't_warm': 10.0, 'n': 6}
    thread = threading.Thread(target=background_worker, args=(params, 'resultados'), daemon=True)
    thread.start()
    flash('Demo iniciada en segundo plano. Revisa el estado en la página.', 'success')
    if request.method == 'POST' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'demo_started'})
    return redirect(url_for('index'))


@app.route('/debug_status')
def debug_status():
    """Devuelve el contenido raw de resultados/status.json para depuración."""
    status_path = os.path.join('resultados', 'status.json')
    if os.path.exists(status_path):
        try:
            with open(status_path, 'r', encoding='utf-8') as f:
                return Response(f.read(), mimetype='application/json')
        except Exception:
            return Response('error reading status', status=500)
    return Response('no status', status=404)


@app.route('/status')
def status():
    status_path = os.path.join('resultados', 'status.json')
    if os.path.exists(status_path):
        try:
            with open(status_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception:
            return jsonify({'phase': 'error', 'message': 'No se puede leer status'}), 500
    return jsonify({'phase': 'idle', 'message': 'Sin ejecuciones'})


@app.route('/download_metrics.csv')
def download_metrics_csv():
    metrics_path = os.path.join('resultados', 'last_metrics.json')
    if not os.path.exists(metrics_path):
        return Response('No metrics available', status=404)

    with open(metrics_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    estad = data.get('estadisticas', {})
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['metric', 'value'])
    rows = [
        ('Wq_promedio', estad.get('Wq_promedio')),
        ('Ws_promedio', estad.get('Ws_promedio')),
        ('Lq_promedio', estad.get('Lq_promedio')),
        ('rho_promedio', estad.get('rho_promedio')),
        ('intervalo_Wq_95', estad.get('intervalo_Wq_95')),
        ('N_replicas', estad.get('N_replicas') or estad.get('N_replicas', None)),
    ]
    for r in rows:
        writer.writerow([r[0], r[1]])

    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=metrics.csv'})


@app.route('/resultados/<path:filename>')
def archivos(filename):
    return send_from_directory('resultados', filename)


@app.route('/results_list')
def results_list():
    """Devuelve JSON con la lista de imágenes en la carpeta `resultados`."""
    resultados_dir = os.path.abspath('resultados')
    archivos = []
    if os.path.isdir(resultados_dir):
        archivos = sorted([f for f in os.listdir(resultados_dir) if any(f.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg'))])
    return jsonify({'images': archivos})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
