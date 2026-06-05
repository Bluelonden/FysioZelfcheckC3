document.addEventListener("DOMContentLoaded", function() {
    
    fetch('/api/patient-data')
        .then(response => response.json())
        .then(data => {
            
            var options = {
                series: [{
                    name: 'PM2.5 Levels',
                    data: data
                }],
                chart: {
                    type: 'candlestick',
                    height: 400,
                    toolbar: {
                        show: false
                    },
                    fontFamily: 'Segoe UI, sans-serif'
                },
                title: {
                    text: 'Air Quality Extremes',
                    align: 'left'
                },
                xaxis: {
                    type: 'datetime'
                },
                yaxis: {
                    tooltip: {
                        enabled: true
                    },
                    title: {
                        text: 'PM 2.5 (µg/m³)'
                    }
                },
                plotOptions: {
                    candlestick: {
                        colors: {
                            upward: '#4299e1', // Blue for better air
                            downward: '#e53e3e' // Red for worse air spikes
                        },
                        wick: {
                            useFillColor: true
                        }
                    }
                }
            };

            // Render the chart in the HTML div
            var chart = new ApexCharts(document.querySelector("#candleChart"), options);
            chart.render();

        })
        .catch(error => console.error('Error fetching JSON data:', error));


});
