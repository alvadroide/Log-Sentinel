import os
import re # ¡La librería clave para Expresiones Regulares!
import json
import requests # Para la geolocalización de IPs
from flask import Flask, render_template, request, jsonify
from collections import Counter # Para contar IPs fácilmente

# --- Configuración Inicial ---
app = Flask(__name__)
# Carpeta para guardar los logs temporalmente
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Asegurarse de que la carpeta 'uploads' exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- La Expresión Regular (Regex) ---
# Esta es la "magia". Busca líneas de "Failed password" en un log de SSH (auth.log)
# y extrae el usuario y la dirección IP.
# Ejemplo de línea: "Oct 23 10:00:00 server sshd[1234]: Failed password for invalid user admin from 123.45.67.89 port 12345 ssh2"
SSH_FAIL_REGEX = re.compile(
    r'Failed password for (?:invalid user )?(.+?) from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
)

# --- Funciones Helper ---

def get_ip_geolocation(ip):
    """ Llama a una API pública para obtener datos de geolocalización de una IP. """
    try:
        # Usamos una API gratuita y sin clave
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=country,countryCode,lat,lon,query')
        response.raise_for_status() # Lanza un error si la petición falla
        data = response.json()
        if data.get('status') == 'success':
            return {
                'ip': data['query'],
                'country': data.get('country', 'Unknown'),
                'country_code': data.get('countryCode', '??'),
                'lat': data.get('lat', 0),
                'lon': data.get('lon', 0)
            }
    except requests.exceptions.RequestException as e:
        print(f"Error al geolocalizar IP {ip}: {e}")
    # Devuelve un objeto por defecto si la API falla
    return {'ip': ip, 'country': 'Unknown', 'country_code': '??', 'lat': 0, 'lon': 0}

def parse_log_file(filepath):
    """ Lee el archivo log y extrae los ataques usando Regex. """
    found_ips = []
    found_users = []
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            match = SSH_FAIL_REGEX.search(line)
            if match:
                # match.group(1) es el usuario
                # match.group(2) es la IP
                found_users.append(match.group(1))
                found_ips.append(match.group(2))
    
    # 1. Contar el total de fallos
    total_failures = len(found_ips)
    
    # 2. Contar las 5 IPs más ofensivas
    # Counter({'1.2.3.4': 50, '5.6.7.8': 20})
    ip_counts = Counter(found_ips)
    top_5_ips = ip_counts.most_common(5) # Lista de tuplas [('1.2.3.4', 50), ...]
    
    # 3. Contar los 5 nombres de usuario más intentados
    user_counts = Counter(found_users)
    top_5_users = user_counts.most_common(5)
    
    # 4. Obtener geolocalización de las IPs top
    geo_data = []
    for ip, count in top_5_ips:
        geo = get_ip_geolocation(ip)
        geo['count'] = count # Añadimos el conteo al objeto
        geo_data.append(geo)

    return {
        'total_failures': total_failures,
        'top_5_ips': top_5_ips,
        'top_5_users': top_5_users,
        'geo_data': geo_data
    }

# --- Rutas de la API ---

@app.route('/')
def index():
    """ Sirve la página principal con el formulario de subida. """
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_log():
    """ Recibe el archivo, lo guarda, lo analiza y devuelve los resultados. """
    if 'log_file' not in request.files:
        return jsonify({'error': 'No se encontró el archivo'}), 400
    
    file = request.files['log_file']
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        
    if file:
        # Guardar el archivo de forma segura
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # Analizar el archivo
        try:
            analysis_results = parse_log_file(filepath)
            # Opcional: Borrar el archivo después de analizarlo
            # os.remove(filepath)
            
            return jsonify(analysis_results)
        except Exception as e:
            # os.remove(filepath)
            return jsonify({'error': f'Error al analizar el archivo: {str(e)}'}), 500

# --- Inicialización ---
if __name__ == '__main__':
    app.run(debug=True)