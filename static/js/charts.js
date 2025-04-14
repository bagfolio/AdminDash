/**
 * Charts.js - Chart initialization and utilities
 */

/**
 * Create a line chart
 * @param {string} canvasId - The canvas element ID
 * @param {Array} labels - The chart labels (x-axis)
 * @param {Array} datasets - The chart datasets
 * @param {Object} options - Additional chart options
 * @returns {Chart} The created chart
 */
function createLineChart(canvasId, labels, datasets, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    
    const ctx = canvas.getContext('2d');
    
    // Default chart options
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        },
        scales: {
            x: {
                ticks: {
                    autoSkip: true,
                    maxRotation: 0
                }
            },
            y: {
                beginAtZero: true
            }
        }
    };
    
    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: chartOptions
    });
}

/**
 * Create a bar chart
 * @param {string} canvasId - The canvas element ID
 * @param {Array} labels - The chart labels (x-axis)
 * @param {Array} datasets - The chart datasets
 * @param {Object} options - Additional chart options
 * @returns {Chart} The created chart
 */
function createBarChart(canvasId, labels, datasets, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    
    const ctx = canvas.getContext('2d');
    
    // Default chart options
    const defaultOptions = {
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
    };
    
    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: chartOptions
    });
}

/**
 * Create a pie chart
 * @param {string} canvasId - The canvas element ID
 * @param {Array} labels - The chart labels
 * @param {Array} data - The chart data
 * @param {Array} backgroundColor - Background colors for segments
 * @param {Object} options - Additional chart options
 * @returns {Chart} The created chart
 */
function createPieChart(canvasId, labels, data, backgroundColor, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    
    const ctx = canvas.getContext('2d');
    
    // Default chart options
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
            }
        }
    };
    
    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColor
            }]
        },
        options: chartOptions
    });
}

/**
 * Create a financial time series chart (stock price chart)
 * @param {string} canvasId - The canvas element ID
 * @param {Array} dates - Array of date strings
 * @param {Array} prices - Array of price data (objects with open, high, low, close)
 * @param {Object} options - Additional chart options
 * @returns {Chart} The created chart
 */
function createStockChart(canvasId, dates, prices, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    
    const ctx = canvas.getContext('2d');
    
    // Prepare data for chart
    const closeData = prices.map(p => p.close);
    
    // Default chart options
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const index = context.dataIndex;
                        const price = prices[index];
                        return [
                            `Open: $${price.open.toFixed(2)}`,
                            `High: $${price.high.toFixed(2)}`,
                            `Low: $${price.low.toFixed(2)}`,
                            `Close: $${price.close.toFixed(2)}`,
                            price.volume ? `Volume: ${price.volume.toLocaleString()}` : null
                        ].filter(Boolean);
                    }
                }
            }
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'day'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Price ($)'
                }
            }
        }
    };
    
    // Merge default options with provided options
    const chartOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Close Price',
                data: closeData,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                fill: true
            }]
        },
        options: chartOptions
    });
}

/**
 * Generate random but visually pleasing colors for charts
 * @param {number} count - Number of colors to generate
 * @param {number} opacity - Color opacity (0-1)
 * @returns {Array} Array of color strings
 */
function generateChartColors(count, opacity = 0.7) {
    const baseColors = [
        [75, 192, 192],   // Teal
        [54, 162, 235],   // Blue
        [255, 99, 132],   // Red
        [255, 159, 64],   // Orange
        [153, 102, 255],  // Purple
        [255, 205, 86],   // Yellow
        [201, 203, 207],  // Grey
        [126, 214, 156]   // Green
    ];
    
    const colors = [];
    for (let i = 0; i < count; i++) {
        // Use base colors first, then generate variations
        if (i < baseColors.length) {
            const [r, g, b] = baseColors[i];
            colors.push(`rgba(${r}, ${g}, ${b}, ${opacity})`);
        } else {
            const [r, g, b] = baseColors[i % baseColors.length];
            // Adjust the color slightly for variation
            const variation = 20 * Math.floor(i / baseColors.length);
            const newR = Math.min(255, Math.max(0, r + variation));
            const newG = Math.min(255, Math.max(0, g - variation));
            const newB = Math.min(255, Math.max(0, b + variation));
            colors.push(`rgba(${newR}, ${newG}, ${newB}, ${opacity})`);
        }
    }
    
    return colors;
}
