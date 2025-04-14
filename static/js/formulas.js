/**
 * Formulas.js - Functionality for custom formula management
 */

// Current formula being edited
let currentFormulaId = null;
let formulaEditor = null;

// Initialize formulas page
document.addEventListener('DOMContentLoaded', function() {
    // Initialize formula list
    initFormulaList();
    
    // Set up event listeners for formula form
    const formulaForm = document.getElementById('formula-form');
    if (formulaForm) {
        formulaForm.addEventListener('submit', submitFormula);
    }
    
    // Initialize calculation form
    const calculateForm = document.getElementById('calculate-form');
    if (calculateForm) {
        calculateForm.addEventListener('submit', calculateFormula);
    }
    
    // Initialize variable selection
    initVariableSelection();
});

/**
 * Initialize the formula list with event handlers
 */
function initFormulaList() {
    // Add event listeners to delete buttons
    document.querySelectorAll('.delete-formula-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const formulaId = this.getAttribute('data-formula-id');
            const formulaName = this.getAttribute('data-formula-name');
            
            // Show confirmation modal
            const modal = document.getElementById('confirm-delete-modal');
            modal.querySelector('.formula-name').textContent = formulaName;
            
            const confirmBtn = modal.querySelector('.confirm-delete-btn');
            confirmBtn.setAttribute('data-formula-id', formulaId);
            confirmBtn.addEventListener('click', deleteFormula);
            
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        });
    });
    
    // Add event listeners to edit buttons
    document.querySelectorAll('.edit-formula-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const formulaId = this.getAttribute('data-formula-id');
            editFormula(formulaId);
        });
    });
    
    // Add event listeners to calculate buttons
    document.querySelectorAll('.calculate-formula-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const formulaId = this.getAttribute('data-formula-id');
            const formulaName = this.getAttribute('data-formula-name');
            
            // Set the formula ID in the calculate form
            document.getElementById('calc-formula-id').value = formulaId;
            document.getElementById('calc-formula-name').textContent = formulaName;
            
            // Show the calculate modal
            const modal = new bootstrap.Modal(document.getElementById('calculate-modal'));
            modal.show();
        });
    });
}

/**
 * Initialize variable selection dropdown
 */
function initVariableSelection() {
    const variableSelect = document.getElementById('variable-select');
    if (!variableSelect) return;
    
    variableSelect.addEventListener('change', function() {
        const selectedVariable = this.value;
        if (!selectedVariable) return;
        
        // Get the formula text element
        const formulaText = document.getElementById('formula-text');
        if (!formulaText) return;
        
        // Insert the variable at the cursor position or at the end
        if (formulaText.selectionStart || formulaText.selectionStart === 0) {
            const startPos = formulaText.selectionStart;
            const endPos = formulaText.selectionEnd;
            formulaText.value = formulaText.value.substring(0, startPos) + 
                selectedVariable + 
                formulaText.value.substring(endPos, formulaText.value.length);
            formulaText.focus();
            formulaText.selectionStart = startPos + selectedVariable.length;
            formulaText.selectionEnd = startPos + selectedVariable.length;
        } else {
            formulaText.value += selectedVariable;
            formulaText.focus();
        }
    });
}

/**
 * Submit a formula create/update form
 * @param {Event} e - The submit event
 */
function submitFormula(e) {
    e.preventDefault();
    
    const form = e.target;
    const formulaName = form.elements['formula-name'].value.trim();
    const formulaDesc = form.elements['formula-description'].value.trim();
    const formulaText = form.elements['formula-text'].value.trim();
    
    if (!formulaName || !formulaText) {
        showAlert('Please enter a formula name and expression.', 'danger');
        return;
    }
    
    // Get variables from formula text
    const variableMatches = formulaText.match(/[a-zA-Z_][a-zA-Z0-9_]*/g) || [];
    const variables = [...new Set(variableMatches)].filter(v => {
        // Filter out common math functions
        return !['sin', 'cos', 'tan', 'log', 'exp', 'pow', 'sqrt', 'abs', 'min', 'max'].includes(v);
    });
    
    // Create formula data object
    const formulaData = {
        name: formulaName,
        description: formulaDesc,
        formula_text: formulaText,
        variables: variables
    };
    
    // Send to server
    fetch('/api/formulas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formulaData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        // Show success message and refresh the page
        showAlert('Formula saved successfully!', 'success');
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    })
    .catch(error => {
        console.error('Error saving formula:', error);
        showAlert(`Error saving formula: ${error.message}`, 'danger');
    });
}

/**
 * Edit an existing formula
 * @param {string} formulaId - The ID of the formula to edit
 */
function editFormula(formulaId) {
    // Get formula data from the DOM
    const formulaCard = document.querySelector(`.formula-card[data-formula-id="${formulaId}"]`);
    if (!formulaCard) return;
    
    const name = formulaCard.querySelector('.formula-name').textContent;
    const description = formulaCard.querySelector('.formula-description').textContent;
    const formulaText = formulaCard.querySelector('.formula-text').textContent;
    
    // Populate the formula form
    document.getElementById('formula-name').value = name;
    document.getElementById('formula-description').value = description;
    document.getElementById('formula-text').value = formulaText;
    
    // Set current formula ID
    currentFormulaId = formulaId;
    
    // Update form title and button text
    document.getElementById('formula-form-title').textContent = 'Edit Formula';
    document.getElementById('formula-submit-btn').textContent = 'Update Formula';
    
    // Scroll to the form
    document.getElementById('formula-form').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Delete a formula
 */
function deleteFormula() {
    const formulaId = this.getAttribute('data-formula-id');
    if (!formulaId) return;
    
    // Close the modal
    bootstrap.Modal.getInstance(document.getElementById('confirm-delete-modal')).hide();
    
    // Show loading
    showAlert('Deleting formula...', 'info');
    
    // Send delete request
    fetch(`/api/formulas/${formulaId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        // Show success message and refresh
        showAlert('Formula deleted successfully!', 'success');
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    })
    .catch(error => {
        console.error('Error deleting formula:', error);
        showAlert(`Error deleting formula: ${error.message}`, 'danger');
    });
}

/**
 * Calculate a formula for specified symbols and date range
 * @param {Event} e - The submit event
 */
function calculateFormula(e) {
    e.preventDefault();
    
    const form = e.target;
    const formulaId = form.elements['calc-formula-id'].value;
    const symbolInput = form.elements['calc-symbols'].value.trim();
    const startDate = form.elements['calc-start-date'].value;
    const endDate = form.elements['calc-end-date'].value;
    
    if (!formulaId || !symbolInput || !startDate) {
        showAlert('Please enter symbols and a start date.', 'danger', 'calc-alert');
        return;
    }
    
    // Parse symbols (comma-separated)
    const symbols = symbolInput.split(',').map(s => s.trim().toUpperCase()).filter(s => s);
    
    if (symbols.length === 0) {
        showAlert('Please enter at least one valid symbol.', 'danger', 'calc-alert');
        return;
    }
    
    // Show loading
    const resultsContainer = document.getElementById('calculation-results');
    resultsContainer.innerHTML = `
        <div class="text-center py-3">
            <div class="spinner-border text-primary"></div>
            <p class="mt-2">Calculating results...</p>
        </div>
    `;
    
    // Send calculation request
    fetch(`/api/formulas/${formulaId}/calculate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbols: symbols,
            start_date: startDate,
            end_date: endDate || undefined
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultsContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }
        
        if (data.results && data.results.length > 0) {
            // Group results by symbol
            const resultsBySymbol = {};
            data.results.forEach(result => {
                const symbolKey = result.symbol || symbols[0];
                if (!resultsBySymbol[symbolKey]) {
                    resultsBySymbol[symbolKey] = [];
                }
                resultsBySymbol[symbolKey].push(result);
            });
            
            // Render results
            let resultHtml = `
                <div class="alert alert-success">${data.message}</div>
                <div class="accordion" id="results-accordion">
            `;
            
            Object.keys(resultsBySymbol).forEach((symbol, index) => {
                const results = resultsBySymbol[symbol];
                resultHtml += `
                    <div class="accordion-item">
                        <h2 class="accordion-header" id="heading-${index}">
                            <button class="accordion-button ${index > 0 ? 'collapsed' : ''}" type="button" 
                                    data-bs-toggle="collapse" data-bs-target="#collapse-${index}" 
                                    aria-expanded="${index === 0 ? 'true' : 'false'}" aria-controls="collapse-${index}">
                                ${symbol} (${results.length} results)
                            </button>
                        </h2>
                        <div id="collapse-${index}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" 
                             aria-labelledby="heading-${index}" data-bs-parent="#results-accordion">
                            <div class="accordion-body">
                                <div class="table-responsive">
                                    <table class="table table-sm table-striped">
                                        <thead>
                                            <tr>
                                                <th>Date</th>
                                                <th>Result</th>
                                                <th>Inputs</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                `;
                
                // Add rows for each result
                results.forEach(result => {
                    resultHtml += `
                        <tr>
                            <td>${result.date}</td>
                            <td>${result.value !== null ? result.value.toFixed(4) : 'N/A'}</td>
                            <td>
                    `;
                    
                    // Add inputs
                    if (result.inputs) {
                        resultHtml += '<ul class="mb-0 ps-3">';
                        Object.entries(result.inputs).forEach(([key, value]) => {
                            resultHtml += `<li><strong>${key}</strong>: ${value}</li>`;
                        });
                        resultHtml += '</ul>';
                    } else {
                        resultHtml += '<span class="text-muted">No input data</span>';
                    }
                    
                    resultHtml += `
                            </td>
                        </tr>
                    `;
                });
                
                resultHtml += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            resultHtml += '</div>';
            resultsContainer.innerHTML = resultHtml;
            
            // Initialize chart
            initResultChart(data.results);
        } else {
            resultsContainer.innerHTML = '<div class="alert alert-info">No results found for the specified criteria.</div>';
        }
    })
    .catch(error => {
        console.error('Error calculating formula:', error);
        resultsContainer.innerHTML = `<div class="alert alert-danger">Error calculating formula: ${error.message}</div>`;
    });
}

/**
 * Initialize chart for formula results
 * @param {Array} results - The calculation results
 */
function initResultChart(results) {
    if (!results || results.length === 0) return;
    
    const chartContainer = document.getElementById('result-chart-container');
    if (!chartContainer) return;
    
    // Group results by symbol
    const resultsBySymbol = {};
    results.forEach(result => {
        const symbolKey = result.symbol || 'unknown';
        if (!resultsBySymbol[symbolKey]) {
            resultsBySymbol[symbolKey] = [];
        }
        resultsBySymbol[symbolKey].push(result);
    });
    
    // Create chart canvas
    chartContainer.innerHTML = '<canvas id="result-chart"></canvas>';
    const ctx = document.getElementById('result-chart').getContext('2d');
    
    // Prepare datasets
    const datasets = [];
    const colors = ['#007bff', '#28a745', '#dc3545', '#fd7e14', '#6f42c1', '#20c997'];
    
    Object.keys(resultsBySymbol).forEach((symbol, index) => {
        const results = resultsBySymbol[symbol].sort((a, b) => new Date(a.date) - new Date(b.date));
        
        datasets.push({
            label: symbol,
            data: results.map(r => ({ x: r.date, y: r.value })),
            backgroundColor: colors[index % colors.length],
            borderColor: colors[index % colors.length],
            tension: 0.1,
            pointRadius: 3
        });
    });
    
    // Create chart
    new Chart(ctx, {
        type: 'line',
        data: {
            datasets
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day'
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Formula Results'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(4)}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Show an alert message
 * @param {string} message - The message to show
 * @param {string} type - The alert type (success, danger, etc.)
 * @param {string} containerId - Optional container ID
 */
function showAlert(message, type = 'info', containerId = 'alert-container') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type} alert-dismissible fade show`;
    alertEl.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.innerHTML = '';
    container.appendChild(alertEl);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
        alert.close();
    }, 5000);
}
