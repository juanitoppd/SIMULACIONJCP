import os
from flask import Flask, send_from_directory, render_template_string

app = Flask(__name__, static_folder='resultados')

TEMPLATE_INDEX = '''
<!doctype html>
<title>Simulación TechClassUC</title>
<h2>Simulación TechClassUC</h2>
<p>Ver gráficas generadas en la carpeta <strong>resultados</strong>:</p>
<ul>
  <li><a href="/resultados/evolucion_temporal.png">Evolución temporal</a></li>
  <li><a href="/resultados/histograma_wq.png">Histograma Wq</a></li>
  <li><a href="/resultados/wq_vs_c.png">Wq vs c</a></li>
  <li><a href="/resultados/rho_vs_lambda.png">ρ vs λ</a></li>
  <li><a href="/resultados/distribucion_medias_wq.png">Distribución de medias</a></li>
</ul>
<p>Si no hay imágenes, ejecuta la simulación en el servidor (o ejecuta <code>python main.py --n 30 --output resultados</code> localmente).</p>
'''


@app.route('/')
def index():
    return render_template_string(TEMPLATE_INDEX)


@app.route('/resultados/<path:filename>')
def archivos(filename):
    return send_from_directory('resultados', filename)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
