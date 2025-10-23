document.addEventListener('DOMContentLoaded', () => {

    const uploadForm = document.getElementById('upload-form');
    const logFileInput = document.getElementById('log-file-input');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorMessage = document.getElementById('error-message');
    const dashboard = document.getElementById('dashboard');

    // Referencias a los elementos del dashboard
    const totalFailuresDisplay = document.getElementById('total-failures');
    const topAttackerDisplay = document.getElementById('top-attacker');
    const topUserDisplay = document.getElementById('top-user');
    const ipChartCanvas = document.getElementById('ip-chart');
    
    // Variables globales para el mapa y el gráfico (para destruirlos al recargar)
    let map = null; // ¡IMPORTANTE QUE map sea global!
    let ipChart = null;

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Evitar que el formulario se envíe de forma tradicional
        
        // Limpiar estado anterior
        loadingSpinner.style.display = 'block';
        errorMessage.textContent = '';
        dashboard.style.display = 'none';
        
        const formData = new FormData();
        formData.append('log_file', logFileInput.files[0]);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Error en el servidor');
            }

            // ¡Éxito! Poblar el dashboard
            populateDashboard(data);
            dashboard.style.display = 'block';

            // --- ¡LA LÍNEA DEL ARREGLO! ---
            // Le dice al mapa: "Oye, ya eres visible, ajusta tu tamaño."
            // Usamos un pequeño timeout para asegurar que el CSS se aplicó.
            setTimeout(() => {
                if (map) {
                    map.invalidateSize();
                }
            }, 10); // 10ms es suficiente

        } catch (error) {
            console.error('Error:', error);
            errorMessage.textContent = `Error: ${error.message}`;
        } finally {
            loadingSpinner.style.display = 'none';
        }
    });

    function populateDashboard(data) {
        // 1. Poblar las tarjetas de resumen
        totalFailuresDisplay.textContent = data.total_failures;
        
        if (data.top_5_ips.length > 0) {
            topAttackerDisplay.textContent = `${data.top_5_ips[0][0]} (${data.top_5_ips[0][1]} intentos)`;
        } else {
            topAttackerDisplay.textContent = 'N/A';
        }

        if (data.top_5_users.length > 0) {
            topUserDisplay.textContent = `${data.top_5_users[0][0]} (${data.top_5_users[0][1]} intentos)`;
        } else {
            topUserDisplay.textContent = 'N/A';
        }

        // 2. Crear el gráfico de IPs
        createIpChart(data.top_5_ips);

        // 3. Crear el mapa
        createMap(data.geo_data);
    }

    function createIpChart(topIps) {
        // Destruir el gráfico anterior si existe
        if (ipChart) {
            ipChart.destroy();
        }
        
        const labels = topIps.map(ip => ip[0]); // Lista de IPs
        const counts = topIps.map(ip => ip[1]); // Lista de conteos

        const ctx = ipChartCanvas.getContext('2d');
        ipChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Nº de Intentos Fallidos',
                    data: counts,
                    backgroundColor: 'rgba(26, 35, 126, 0.7)',
                    borderColor: 'rgba(26, 35, 126, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    function createMap(geoData) {
        // Destruir el mapa anterior si existe
        if (map !== null) {
            map.remove();
        }
        
        // Inicializar el mapa
        map = L.map('map').setView([47.0, 2.0], 3); // Centrado en Europa

        // Añadir la capa de "tiles" (el fondo del mapa)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        // Añadir un marcador por cada IP geolocalizada
        geoData.forEach(ipData => {
            if (ipData.lat !== 0 && ipData.lon !== 0) { 
                L.marker([ipData.lat, ipData.lon]).addTo(map)
                    .bindPopup(`<b>${ipData.ip}</b><br>${ipData.country}<br>${ipData.count} intentos.`);
            }
        });
    }
});