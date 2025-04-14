/**
 * Dashboard.js - Functionality for the main dashboard
 */

// Initialize dashboard charts and components
document.addEventListener('DOMContentLoaded', function() {
    initDashboardStats();
    initActivityLog();
    initRecentDataChart();
});

/**
 * Initialize dashboard statistics with animations
 */
function initDashboardStats() {
    // Get all stat counters
    const counters = document.querySelectorAll('.stat-value');
    
    // Animate each counter from 0 to its final value
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-value'), 10);
        let count = 0;
        const duration = 1000; // 1 second animation
        const step = Math.max(1, Math.floor(target / (duration / 30))); // Update roughly every 30ms
        
        const updateCounter = () => {
            count += step;
            if (count >= target) {
                counter.textContent = target.toLocaleString();
                return;
            }
            counter.textContent = count.toLocaleString();
            requestAnimationFrame(updateCounter);
        };
        
        updateCounter();
    });
}

/**
 * Initialize activity log table with DataTables
 */
function initActivityLog() {
    if (document.getElementById('activity-log-table')) {
        $('#activity-log-table').DataTable({
            pageLength: 5,
            lengthChange: false,
            info: false,
            searching: false,
            order: [[0, 'desc']], // Sort by timestamp descending
            columnDefs: [
                { 
                    targets: -1, // Status column (last)
                    render: function(data, type, row) {
                        if (type === 'display') {
                            if (data === 'Success') {
                                return '<span class="badge bg-success">Success</span>';
                            } else {
                                return '<span class="badge bg-danger">Failed</span>';
                            }
                        }
                        return data;
                    }
                }
            ]
        });
    }
}

/**
 * Initialize recent data chart
 */
function initRecentDataChart() {
    const ctx = document.getElementById('recent-data-chart');
    
    if (!ctx) return;
    
    // Sample data - in real app this would come from API
    const chartData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [
            {
                label: 'API Calls',
                backgroundColor: 'rgba(0, 123, 255, 0.5)',
                borderColor: 'rgba(0, 123, 255, 1)',
                data: [12, 19, 3, 5, 2, 3],
                fill: true,
                tension: 0.4
            },
            {
                label: 'Records Stored',
                backgroundColor: 'rgba(40, 167, 69, 0.5)',
                borderColor: 'rgba(40, 167, 69, 1)',
                data: [52, 39, 32, 51, 62, 33],
                fill: true,
                tension: 0.4
            }
        ]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'API Activity'
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

/**
 * Reload dashboard data
 */
function refreshDashboard() {
    // Show loading spinner
    document.getElementById('refresh-spinner').classList.remove('d-none');
    
    // Simulate data refresh - replace with actual API call
    setTimeout(() => {
        // Hide loading spinner
        document.getElementById('refresh-spinner').classList.add('d-none');
        
        // Show success message
        const toast = new bootstrap.Toast(document.getElementById('refresh-toast'));
        toast.show();
        
        // Reload page data
        window.location.reload();
    }, 1500);
}
