// static/js/admin/analytics.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    let trendChart = null;
    let categoryChart = null;

    // Fetch analytics data
    function fetchAnalytics() {
    fetch('/quiz-admin/api/dashboard-stats/')  // This matches your urls.py configuration
        .then(response => response.json())
        .then(data => {
            updateDashboard(data);
        })
        .catch(error => console.error('Error fetching analytics:', error));
    }

    // Update dashboard with new data
    function updateDashboard(data) {
        // Update stats cards
        document.getElementById('totalUsers').textContent = data.overview.total_users;
        document.getElementById('totalQuizzes').textContent = data.overview.total_quizzes;
        document.getElementById('totalAttempts').textContent = data.overview.total_attempts;
        document.getElementById('avgScore').textContent = `${data.overview.avg_score}%`;

        // Update trend chart
        updateTrendChart(data.trends);

        // Update category chart
        updateCategoryChart(data.categoryPerformance);

        // Update recent activity table
        updateRecentActivity(data.recentActivity);
    }

    // Initialize and update trend chart
    function updateTrendChart(trendsData) {
        const ctx = document.getElementById('trendChart').getContext('2d');
        
        const labels = trendsData.map(item => item.date);
        const attempts = trendsData.map(item => item.attempts);

        if (trendChart) {
            trendChart.destroy();
        }

        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Quiz Attempts',
                    data: attempts,
                    borderColor: '#0D9488',
                    tension: 0.4,
                    fill: true,
                    backgroundColor: 'rgba(13, 148, 136, 0.1)'
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
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Initialize and update category chart
    function updateCategoryChart(categoryData) {
        const ctx = document.getElementById('categoryChart').getContext('2d');
        
        const labels = categoryData.map(item => item.name);
        const avgScores = categoryData.map(item => item.avgScore);
        const attempts = categoryData.map(item => item.totalAttempts);

        if (categoryChart) {
            categoryChart.destroy();
        }

        categoryChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Average Score',
                        data: avgScores,
                        backgroundColor: 'rgba(13, 148, 136, 0.8)',
                        yAxisID: 'y'
                    },
                    {
                        label: 'Total Attempts',
                        data: attempts,
                        backgroundColor: 'rgba(255, 138, 76, 0.8)',
                        yAxisID: 'y1'
                    }
                ]
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
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Average Score'
                        }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Total Attempts'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }

    // Update recent activity table
    function updateRecentActivity(activities) {
        const tbody = document.getElementById('recentActivityTable');
        tbody.innerHTML = '';

        activities.forEach(activity => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${activity.user}</td>
                <td>${activity.quiz}</td>
                <td>
                    <span class="badge bg-${activity.score >= 70 ? 'success' : 'warning'}">
                        ${activity.score}%
                    </span>
                </td>
                <td>${formatTime(activity.time_taken)}</td>
                <td>${formatDate(activity.completed_at)}</td>
            `;
            tbody.appendChild(row);
        });
    }

    // Helper function to format time
    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds}s`;
    }

    // Helper function to format date
    function formatDate(dateString) {
        return new Date(dateString).toLocaleString();
    }

    // Initial fetch
    fetchAnalytics();

    // Refresh data every 30 seconds
    setInterval(fetchAnalytics, 30000);
});
