document.addEventListener("DOMContentLoaded", function() {
    
    // 1. Zoek het canvas-element in je HTML
    const ctx = document.getElementById("pm25_graph");
    if (!ctx) {
        console.error("Kan het element #pm25_graph niet vinden in de HTML! Zorg dat dit een <canvas> is.");
        return;
    }

    // 2. Maak de Chart.js lijngrafiek aan met een lege start-status
    const pm25Chart = new Chart(ctx.getContext("2d"), {
        type: 'line',
        data: {
            labels: [], // Wordt dynamisch gevuld op basis van de hoeveelheid binnengekomen data
            datasets: [{
                label: 'PM2.5 Levels (µg/m³)',
                data: [], // Hier komt de binnengekomen JSON-lijst in te staan
                borderColor: '#4299e1', 
                backgroundColor: 'rgba(66, 153, 225, 0.2)', 
                borderWidth: 2,
                tension: 0.2,
                pointRadius: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'PM 2.5 (µg/m³)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Metingen'
                    }
                }
            }
        }
    });

    // 3. Haal de data op van jouw specifieke link
    fetch('/api/patient-data')
        .then(response => response.json())
        .then(data => {
            // Controleer of de data een array (lijst) is
            if (Array.isArray(data)) {
                
                // Genereer automatische labels op basis van de index (Meting 1, Meting 2, etc.)
                // Dit voorkomt dat Chart.js crasht omdat er geen x-as labels zijn.
                const gegenereerdeLabels = data.map((_, index) => `Meting ${index + 1}`);

                // Stop de data en de labels in de grafiek
                pm25Chart.data.labels = gegenereerdeLabels;
                pm25Chart.data.datasets[0].data = data;

                // Teken de grafiek opnieuw met de actuele data
                pm25Chart.update();
                
            } else {
                console.error("De API gaf data terug, maar het was geen lijst van metingen:", data);
            }
        })
        .catch(error => console.error('Error fetching JSON data van /api/patient-data:', error));
});