from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrap', methods=['POST'])
def scrap():
    keyword = request.form['keyword']
    year = request.form['year']
    norm_type = request.form['normType']
    
    # Aquí realizas el scraping (esto es solo un ejemplo simplificado)
    url = f"https://www.boletinoficial.gob.ar/{norm_type.lower()}?q={keyword}&year={year}"
    
    # Simulación de datos de respuesta
    scraped_data = {
        'keyword': keyword,
        'year': year,
        'norm_type': norm_type,
        'url': url,
        'results': [
            {'title': 'Resolución 123', 'description': 'Descripción de la resolución'},
            {'title': 'Disposición 456', 'description': 'Descripción de la disposición'}
        ]
    }
    
    return jsonify(scraped_data)

if __name__ == '__main__':
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

