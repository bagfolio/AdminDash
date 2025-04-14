/**
 * Database.js - Functionality for database management page
 */

// Current table being viewed
let currentTable = '';
let currentPage = 1;
let pageSize = 25;
let totalRows = 0;
let dataTable = null;

// Initialize database page
document.addEventListener('DOMContentLoaded', function() {
    // Get initially selected table
    const tableSelect = document.getElementById('table-select');
    if (tableSelect) {
        currentTable = tableSelect.value;
        loadTableData(currentTable, 1);
        
        // Add event listener for table change
        tableSelect.addEventListener('change', function() {
            currentTable = this.value;
            currentPage = 1;
            loadTableData(currentTable, currentPage);
        });
    }
    
    // Initialize query editor if it exists
    const queryEditor = document.getElementById('query-editor');
    if (queryEditor) {
        // Set up event listener for execute query button
        document.getElementById('execute-query-btn').addEventListener('click', executeQuery);
    }
});

/**
 * Load data for the specified table
 * @param {string} tableName - The table name to load
 * @param {number} page - The page number to load
 */
function loadTableData(tableName, page) {
    if (!tableName) return;
    
    // Show loading indicator
    const tableContainer = document.getElementById('table-data-container');
    tableContainer.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div><p class="mt-2">Loading data...</p></div>';
    
    // Fetch data from API
    fetch(`/api/table_data?table=${encodeURIComponent(tableName)}&page=${page}&limit=${pageSize}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                tableContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            renderTableData(data.data, tableName);
            totalRows = data.total;
            currentPage = data.page;
            updatePagination();
        })
        .catch(error => {
            console.error('Error loading table data:', error);
            tableContainer.innerHTML = `<div class="alert alert-danger">Error loading data: ${error.message}</div>`;
        });
}

/**
 * Render table data to the DOM
 * @param {Array} data - The data to render
 * @param {string} tableName - The name of the table
 */
function renderTableData(data, tableName) {
    const tableContainer = document.getElementById('table-data-container');
    
    if (!data || data.length === 0) {
        tableContainer.innerHTML = '<div class="alert alert-info">No data found in this table.</div>';
        return;
    }
    
    // Create table element
    let tableHtml = `
        <div class="table-responsive">
            <table id="database-table" class="table table-striped table-hover">
                <thead class="table-dark">
                    <tr>
    `;
    
    // Add headers
    const columns = Object.keys(data[0]);
    columns.forEach(column => {
        tableHtml += `<th>${column}</th>`;
    });
    
    tableHtml += `
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add rows
    data.forEach(row => {
        tableHtml += '<tr>';
        columns.forEach(column => {
            let cellValue = row[column];
            
            // Format the cell value for display
            if (cellValue === null || cellValue === undefined) {
                cellValue = '<span class="text-muted">NULL</span>';
            } else if (typeof cellValue === 'object') {
                // Pretty-format JSON data
                cellValue = `<code class="small">${JSON.stringify(cellValue, null, 2)}</code>`;
            }
            
            tableHtml += `<td>${cellValue}</td>`;
        });
        tableHtml += '</tr>';
    });
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    // Add table to container
    tableContainer.innerHTML = tableHtml;
    
    // Initialize DataTable for client-side filtering
    if (dataTable) {
        dataTable.destroy();
    }
    
    dataTable = $('#database-table').DataTable({
        paging: false, // We handle paging ourselves
        ordering: true,
        searching: true,
        info: false
    });
}

/**
 * Update pagination controls
 */
function updatePagination() {
    const totalPages = Math.ceil(totalRows / pageSize);
    const paginationEl = document.getElementById('table-pagination');
    
    if (!paginationEl) return;
    
    let paginationHtml = `
        <nav aria-label="Table pagination">
            <ul class="pagination justify-content-center">
                <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">Previous</a>
                </li>
    `;
    
    // Generate page links
    const maxPages = 5; // Maximum number of page links to show
    const startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
    const endPage = Math.min(totalPages, startPage + maxPages - 1);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    paginationHtml += `
                <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">Next</a>
                </li>
            </ul>
        </nav>
    `;
    
    paginationEl.innerHTML = paginationHtml;
}

/**
 * Change the current page
 * @param {number} page - The page number to navigate to
 */
function changePage(page) {
    if (page < 1 || page > Math.ceil(totalRows / pageSize)) return;
    
    currentPage = page;
    loadTableData(currentTable, currentPage);
}

/**
 * Execute a custom SQL query
 */
function executeQuery() {
    const queryText = document.getElementById('query-editor').value.trim();
    const resultsContainer = document.getElementById('query-results');
    
    if (!queryText) {
        resultsContainer.innerHTML = '<div class="alert alert-warning">Please enter a SQL query to execute.</div>';
        return;
    }
    
    // Show loading indicator
    resultsContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary"></div><p class="mt-2">Executing query...</p></div>';
    
    // Send query to server
    fetch('/api/execute_query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: queryText })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultsContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }
        
        if (data.data) {
            // Display results for SELECT queries
            let tableHtml = `
                <div class="alert alert-success">Query executed successfully. ${data.rowCount} rows returned.</div>
                <div class="table-responsive">
                    <table class="table table-sm table-striped table-hover">
                        <thead class="table-dark">
                            <tr>
            `;
            
            // Add headers
            if (data.data.length > 0) {
                const columns = Object.keys(data.data[0]);
                columns.forEach(column => {
                    tableHtml += `<th>${column}</th>`;
                });
                
                tableHtml += `
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                // Add rows
                data.data.forEach(row => {
                    tableHtml += '<tr>';
                    columns.forEach(column => {
                        let cellValue = row[column];
                        
                        // Format the cell value for display
                        if (cellValue === null || cellValue === undefined) {
                            cellValue = '<span class="text-muted">NULL</span>';
                        } else if (typeof cellValue === 'object') {
                            // Pretty-format JSON data
                            cellValue = `<code class="small">${JSON.stringify(cellValue, null, 2)}</code>`;
                        }
                        
                        tableHtml += `<td>${cellValue}</td>`;
                    });
                    tableHtml += '</tr>';
                });
                
                tableHtml += `
                        </tbody>
                    </table>
                </div>
                `;
                
                resultsContainer.innerHTML = tableHtml;
            } else {
                resultsContainer.innerHTML = '<div class="alert alert-info">Query executed successfully, but no rows were returned.</div>';
            }
        } else {
            // Display success message for non-SELECT queries
            resultsContainer.innerHTML = `
                <div class="alert alert-success">
                    Query executed successfully. ${data.rowCount} rows affected.
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error executing query:', error);
        resultsContainer.innerHTML = `<div class="alert alert-danger">Error executing query: ${error.message}</div>`;
    });
}
