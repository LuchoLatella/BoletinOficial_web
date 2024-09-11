# /api/api.py
from flask import Flask, request, jsonify

app = Flask(__name__)

# Endpoint para obtener datos por palabras clave, año, y tipo de norma
@app.route('/api/obtener_datos', methods=['GET'])
def obtener_datos():
    palabra_clave = request.args.get('palabra_clave')
    anio = request.args.get('anio')
    tipo_norma = request.args.get('tipo_norma')

    if not palabra_clave or not anio or not tipo_norma:
        return jsonify({'error': 'Parámetros insuficientes'}), 400

    # Simulación de búsqueda de datos (puedes conectar esto con una base de datos)
    resultados = buscar_datos(palabra_clave, anio, tipo_norma)
    
    return jsonify(resultados), 200

# Función simulada para buscar datos (reemplazar con lógica real)
def buscar_datos(palabra_clave, anio, tipo_norma):
    # Simular algunos resultados según los parámetros
    datos_simulados = {
        "palabra_clave": palabra_clave,
        "anio": anio,
        "tipo_norma": tipo_norma,
        "resultados": [
            {"documento": "RESOLUCIÓN 123", "fecha": f"{anio}-05-15", "detalles": "Aprobación de presupuesto."},
            {"documento": "DISPOSICIÓN 456", "fecha": f"{anio}-06-10", "detalles": "Regulación de tarifas."},
        ]
    }
    return datos_simulados

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
