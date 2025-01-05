// static/js/admin/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    // Updated URL to match the correct endpoint
    fetch('/quiz-admin/api/dashboard-stats/')
        .then(response => response.json())
        .then(data => {
            updateCharts(data);
            updateTopUsers(data.topUsers);
            document.getElementById('todayAttempts').textContent = 
                data.overview.total_quizzes_taken;
        })
        .catch(error => console.error('Error fetching dashboard stats:', error));

    function updateCharts(data) {
        // Trend Chart
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: data.trends.map(t => t.date),
                datasets: [{
                    label: 'Quiz Attempts',
                    data: data.trends.map(t => t.attempts),
                    borderColor: '#0D9488',
                    backgroundColor: 'rgba(13, 148, 136, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });

        // Category Chart
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: data.categoryPerformance.map(c => c.name),
                datasets: [{
                    data: data.categoryPerformance.map(c => c.totalAttempts),
                    backgroundColor: [
                        '#0D9488', '#FF8A4C', '#FFD700', '#2D3748',
                        '#8B5CF6', '#EC4899', '#14B8A6', '#F59E0B'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }

    function updateTopUsers(users) {
        const tbody = document.querySelector('#topUsersTable tbody');
        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.username}</td>
                <td>${user.quizCount}</td>
                <td>${user.avgScore.toFixed(1)}%</td>
            </tr>
        `).join('');
    }
});


