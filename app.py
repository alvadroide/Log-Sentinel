import os
import re 
import json
import requests # Para la geolocalización de IPs
from flask import Flask, render_template, request, jsonify
from collections import Counter 

# --- Configuración Inicial ---
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- La Expresión Regular (Regex) ---
SSH_FAIL_REGEX = re.compile(
    r'Failed password for (?:invalid user )?(.+?) from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
)

# --- Funciones Helper ---

def get_ip_geolocation(ip):
    """ Llama a una API pública para obtener datos de geolocalización de una IP. """
    try:
        # Aumentamos el timeout para conexiones lentas y pedimos 'status'
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,countryCode,lat,lon,query', timeout=5)
        response.raise_for_status() # Lanza un error si la petición falla
        data = response.json()
        
        # --- DEBUGGING ---
        # (Puedes descomentar esta línea para ver la respuesta en tu terminal)
        # print(f"Respuesta de API para {ip}: {data}") 
        # --- FIN DEBUGGING ---

        if data.get('status') == 'success':
            return {
                'ip': data['query'],
                'country': data.get('country', 'Unknown'),
                'country_code': data.get('countryCode', '??'),
                # Usamos 'or 0' para manejar si la API devuelve 'null'
                'lat': data.get('lat') or 0,
                'lon': data.get('lon') or 0
            }
    except requests.exceptions.RequestException as e:
        # --- ¡ESTE ES EL CAMBIO IMPORTANTE! ---
        # ¡Esto nos dirá el error exacto en tu terminal!
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"ERROR: No se pudo geolocalizar la IP {ip}.")
        print(f"Detalle del error: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    
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
                found_users.append(match.group(1))
                found_ips.append(match.group(2))
    
    total_failures = len(found_ips)
    ip_counts = Counter(found_ips)
    top_5_ips = ip_counts.most_common(5) 
    user_counts = Counter(found_users)
    top_5_users = user_counts.most_common(5)
    
    geo_data = []
    
    # Usamos un set para no preguntar por la misma IP dos veces
    unique_top_ips = {ip for ip, count in top_5_ips} 
    
    for ip in unique_top_ips:
        geo = get_ip_geolocation(ip)
        # Re-añadimos el conteo
        geo['count'] = ip_counts[ip] 
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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        try:
            analysis_results = parse_log_file(filepath)
            # os.remove(filepath) # Opcional: Borrar el archivo
            return jsonify(analysis_results)
        except Exception as e:
            # os.remove(filepath) # Opcional: Borrar el archivo
            return jsonify({'error': f'Error al analizar el archivo: {str(e)}'}), 500

# --- Inicialización ---
if __name__ == '__main__':
    app.run(debug=True)