document.addEventListener("DOMContentLoaded", () => {

    // =========================
    // Revenue Line Chart
    // =========================

    const salesLabelsElement = document.getElementById("sales-labels");
    const salesDataElement = document.getElementById("sales-data");
    const transactionCanvas = document.getElementById("transactionChart");

    if (salesLabelsElement && salesDataElement && transactionCanvas) {

        const salesLabels = JSON.parse(salesLabelsElement.textContent);
        const salesData = JSON.parse(salesDataElement.textContent);

        if (salesLabels.length && salesData.length) {

            new Chart(transactionCanvas, {
                type: "line",
                data: {
                    labels: salesLabels,
                    datasets: [{
                        label: "Daily Revenue",
                        data: salesData,
                        borderColor: "#2563eb",
                        backgroundColor: "rgba(37,99,235,0.15)",
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: "top"
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                maxTicksLimit: 10
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function (value) {
                                    return "$" + Number(value).toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // =========================
    // Alert Doughnut Chart
    // =========================

    const alertLabelsElement = document.getElementById("alert-labels");
    const alertDataElement = document.getElementById("alert-data");
    const alertCanvas = document.getElementById("alertChart");

    if (alertLabelsElement && alertDataElement && alertCanvas) {

        const alertLabels = JSON.parse(alertLabelsElement.textContent);
        const alertData = JSON.parse(alertDataElement.textContent);

        if (alertLabels.length && alertData.length) {

            new Chart(alertCanvas, {
                type: "doughnut",
                data: {
                    labels: alertLabels,
                    datasets: [{
                        data: alertData,
                        backgroundColor: [
                            "#dc2626",
                            "#f59e0b",
                            "#3b82f6",
                            "#16a34a"
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom"
                        }
                    }
                }
            });
        }
    }

});