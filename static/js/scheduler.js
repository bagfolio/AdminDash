/**
 * Scheduler.js - Functionality for scheduled tasks
 */

// Initialize scheduler page
document.addEventListener('DOMContentLoaded', function() {
    initTaskForm();
    initTaskList();
});

/**
 * Initialize task creation form
 */
function initTaskForm() {
    const taskForm = document.getElementById('task-form');
    if (!taskForm) return;
    
    taskForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const taskName = document.getElementById('task-name').value.trim();
        const endpointId = document.getElementById('endpoint-select').value;
        const frequency = document.getElementById('task-frequency').value;
        const parameters = getParametersFromForm();
        
        if (!taskName || !endpointId || !frequency) {
            showAlert('Please fill in all required fields.', 'danger');
            return;
        }
        
        // Create task data object
        const taskData = {
            name: taskName,
            endpoint_id: endpointId,
            parameters: parameters,
            frequency: frequency
        };
        
        // Send to server
        fetch('/api/scheduler/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert(data.error, 'danger');
                return;
            }
            
            // Show success message and refresh the page
            showAlert('Task scheduled successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        })
        .catch(error => {
            console.error('Error scheduling task:', error);
            showAlert(`Error scheduling task: ${error.message}`, 'danger');
        });
    });
    
    // Handle endpoint selection change to show appropriate parameters
    const endpointSelect = document.getElementById('endpoint-select');
    if (endpointSelect) {
        endpointSelect.addEventListener('change', function() {
            updateParameterForm(this.value);
        });
        
        // Initialize parameter form for default selection
        updateParameterForm(endpointSelect.value);
    }
}

/**
 * Initialize task list with event handlers
 */
function initTaskList() {
    // Add event listeners to delete buttons
    document.querySelectorAll('.delete-task-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const taskId = this.getAttribute('data-task-id');
            const taskName = this.getAttribute('data-task-name');
            
            // Show confirmation modal
            const modal = document.getElementById('confirm-delete-modal');
            modal.querySelector('.task-name').textContent = taskName;
            
            const confirmBtn = modal.querySelector('.confirm-delete-btn');
            confirmBtn.setAttribute('data-task-id', taskId);
            confirmBtn.addEventListener('click', deleteTask);
            
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        });
    });
    
    // Format dates in a human-friendly way
    document.querySelectorAll('.format-date').forEach(el => {
        const timestamp = el.getAttribute('data-timestamp');
        if (timestamp) {
            const date = new Date(timestamp);
            el.textContent = date.toLocaleString();
        }
    });
}

/**
 * Update parameter form based on selected endpoint
 * @param {string} endpointId - The selected endpoint ID
 */
function updateParameterForm(endpointId) {
    if (!endpointId) return;
    
    const paramContainer = document.getElementById('parameter-container');
    if (!paramContainer) return;
    
    // Get endpoint data from the data attributes
    const endpointSelect = document.getElementById('endpoint-select');
    const selectedOption = endpointSelect.options[endpointSelect.selectedIndex];
    
    if (!selectedOption) {
        paramContainer.innerHTML = '<div class="alert alert-info">No parameters required</div>';
        return;
    }
    
    const parameters = selectedOption.getAttribute('data-parameters');
    if (!parameters) {
        paramContainer.innerHTML = '<div class="alert alert-info">No parameters required</div>';
        return;
    }
    
    try {
        const params = JSON.parse(parameters);
        
        // Build parameter form fields
        let paramHtml = '<div class="mt-3"><h5>Parameters</h5>';
        
        Object.entries(params).forEach(([paramName, paramInfo]) => {
            const isRequired = paramInfo.required;
            
            paramHtml += `
                <div class="mb-3">
                    <label for="param-${paramName}" class="form-label">
                        ${paramName} ${isRequired ? '<span class="text-danger">*</span>' : ''}
                    </label>
            `;
            
            if (paramInfo.options) {
                // Select dropdown for options
                paramHtml += `
                    <select class="form-select" id="param-${paramName}" name="param-${paramName}" 
                            ${isRequired ? 'required' : ''}>
                `;
                
                paramInfo.options.forEach(option => {
                    const isDefault = option === paramInfo.default;
                    paramHtml += `
                        <option value="${option}" ${isDefault ? 'selected' : ''}>${option}</option>
                    `;
                });
                
                paramHtml += '</select>';
            } else {
                // Text input for other parameters
                paramHtml += `
                    <input type="${paramInfo.type === 'integer' ? 'number' : 'text'}" 
                           class="form-control" id="param-${paramName}" name="param-${paramName}"
                           placeholder="${paramInfo.description || ''}"
                           ${isRequired ? 'required' : ''}
                           ${paramInfo.default ? `value="${paramInfo.default}"` : ''}>
                `;
            }
            
            // Add description if available
            if (paramInfo.description) {
                paramHtml += `
                    <div class="form-text">${paramInfo.description}</div>
                `;
            }
            
            paramHtml += '</div>';
        });
        
        paramHtml += '</div>';
        paramContainer.innerHTML = paramHtml;
        
    } catch (error) {
        console.error('Error parsing parameters:', error);
        paramContainer.innerHTML = '<div class="alert alert-danger">Error loading parameters</div>';
    }
}

/**
 * Get parameters from the form inputs
 * @returns {Object} Parameters object
 */
function getParametersFromForm() {
    const params = {};
    const paramContainer = document.getElementById('parameter-container');
    if (!paramContainer) return params;
    
    // Get all parameter inputs
    const paramInputs = paramContainer.querySelectorAll('input, select');
    paramInputs.forEach(input => {
        const paramName = input.name.replace('param-', '');
        let value = input.value;
        
        // Convert to appropriate type if needed
        if (input.type === 'number') {
            value = parseInt(value, 10);
        }
        
        if (paramName && value) {
            params[paramName] = value;
        }
    });
    
    return params;
}

/**
 * Delete a scheduled task
 */
function deleteTask() {
    const taskId = this.getAttribute('data-task-id');
    if (!taskId) return;
    
    // Close the modal
    bootstrap.Modal.getInstance(document.getElementById('confirm-delete-modal')).hide();
    
    // Show loading
    showAlert('Deleting task...', 'info');
    
    // Send delete request
    fetch(`/api/scheduler/tasks/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        // Show success message and refresh
        showAlert('Task deleted successfully!', 'success');
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    })
    .catch(error => {
        console.error('Error deleting task:', error);
        showAlert(`Error deleting task: ${error.message}`, 'danger');
    });
}

/**
 * Show an alert message
 * @param {string} message - The message to show
 * @param {string} type - The alert type (success, danger, etc.)
 */
function showAlert(message, type = 'info') {
    const container = document.getElementById('alert-container');
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
