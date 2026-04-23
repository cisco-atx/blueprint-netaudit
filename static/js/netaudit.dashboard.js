/**
 * netaudit.dashboard.js
 *
 * This JavaScript file is responsible for rendering the Donut Chart and Timeline Chart on the NetAudit dashboard using Chart.js.
 * It listens for the DOMContentLoaded event to ensure that the charts are rendered after the HTML content is fully loaded.
 * The data for both charts is expected to be provided in the global variables `donutData` and `timelineData`, which should be defined in the HTML template.
 * The Donut Chart visualizes the pass/fail status of various checks, while the Timeline Chart shows trends over time for different views.
 */

document.addEventListener('DOMContentLoaded', () => {

    // Prepare data for the Donut Chart
    const donutLabels = Object.keys(donutData.pass);
    const donutPass = donutLabels.map(label => donutData.pass[label]);
    const donutFail = donutLabels.map(label => donutData.fail[label]);

    const donutCtx = document.getElementById('donutChart').getContext('2d');

    new Chart(donutCtx, {
        type: 'doughnut',
        data: {
            labels: donutLabels,
            datasets: [
                {
                    label: 'Pass',
                    data: donutPass,
                    backgroundColor: ['#10A37F', '#0B7285', '#F5A524'],
                    borderWidth: 2
                },
                {
                    label: 'Fail',
                    data: donutFail,
                    backgroundColor: ['#FF5A5F', '#FF8C42', '#ADB5BD'],
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            cutout: '60%', // Donut hole size
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { usePointStyle: true }
                },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            return `${ctx.dataset.label}: ${ctx.parsed}`;
                        }
                    }
                }
            }
        }
    });

    // Prepare data for the Timeline Chart
    const timelineLabels = [...new Set(Object.values(timelineData).flatMap(d => Object.keys(d)))];

    // Create datasets for each view in timelineData
    const timelineDatasets = Object.keys(timelineData).map((view, i) => {
        const months = timelineLabels.map(month => timelineData[view][month] || 0);
        const colors = ['#10A37F', '#0B7285', '#F5A524'];

        return {
            label: view,
            data: months,
            borderColor: colors[i],
            backgroundColor: colors[i] + '33',
            tension: 0.3,
            pointRadius: 4
        };
    });

    const timelineCtx = document.getElementById('timelineChart').getContext('2d');

    new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: timelineLabels,
            datasets: timelineDatasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    grid: { color: '#E9ECEF' }
                },
                x: { grid: { color: '#E9ECEF' } }
            }
        }
    });

});