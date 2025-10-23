Sube un log de servidor (como `auth.log` de Linux) y la aplicación generará un dashboard interactivo que muestra:
* Total de intentos de acceso fallidos.
* Las 5 IPs más ofensivas.
* Un gráfico de barras (Chart.js) de los principales atacantes.
* Un mapa (cLeaflet.js) que geolocaliza el origen de los ataques.

---

* Backend (Python/Flask): Manejo de subida de archivos y creación de un API REST.
* Análisis de Datos (Regex): Uso de Expresiones Regulares para parsear líneas de log complejas y extraer datos de amenazas.
* Integración de APIs: Conexión a la API de `ip-api.com` para geolocalización de IPs.
* Frontend (JavaScript): Peticiones asíncronas (`fetch`) y manipulación del DOM.
* Visualización de Datos: Implementación de Chart.js y Leaflet.js para crear un dashboard dinámico.

<img width="1256" height="557" alt="image" src="https://github.com/user-attachments/assets/b8896b3b-09e1-4d17-b455-bbd5da300bd6" />
