// Dersa EcoQuality - Main Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Auto-calculate efficiency
    const consumptionInput = document.getElementById('consumption_kwh');
    const targetInput = document.getElementById('target_consumption');
    const efficiencyDisplay = document.getElementById('efficiency_display');

    if (consumptionInput && targetInput && efficiencyDisplay) {
        function calculateEfficiency() {
            const consumption = parseFloat(consumptionInput.value);
            const target = parseFloat(targetInput.value);
            
            if (consumption && target && consumption > 0) {
                const efficiency = ((target / consumption) * 100).toFixed(1);
                efficiencyDisplay.textContent = `Efficiency: ${efficiency}%`;
                
                // Color code the efficiency
                if (efficiency >= 85) {
                    efficiencyDisplay.className = 'text-success';
                } else if (efficiency >= 70) {
                    efficiencyDisplay.className = 'text-warning';
                } else {
                    efficiencyDisplay.className = 'text-danger';
                }
            } else {
                efficiencyDisplay.textContent = '';
            }
        }

        consumptionInput.addEventListener('input', calculateEfficiency);
        targetInput.addEventListener('input', calculateEfficiency);
    }

    // Auto-calculate recycling percentage
    const wasteQuantityInput = document.getElementById('quantity_kg');
    const recyclingInput = document.getElementById('recycling_percentage');
    const recyclingAmountDisplay = document.getElementById('recycling_amount_display');

    if (wasteQuantityInput && recyclingInput && recyclingAmountDisplay) {
        function calculateRecyclingAmount() {
            const quantity = parseFloat(wasteQuantityInput.value);
            const percentage = parseFloat(recyclingInput.value);
            
            if (quantity && percentage) {
                const recycledAmount = ((quantity * percentage) / 100).toFixed(2);
                recyclingAmountDisplay.textContent = `Recycled: ${recycledAmount} kg`;
            } else {
                recyclingAmountDisplay.textContent = '';
            }
        }

        wasteQuantityInput.addEventListener('input', calculateRecyclingAmount);
        recyclingInput.addEventListener('input', calculateRecyclingAmount);
    }

    // Defect type change handler
    const defectTypeSelect = document.getElementById('defect_type');
    const defectCountInput = document.getElementById('defect_count');

    if (defectTypeSelect && defectCountInput) {
        defectTypeSelect.addEventListener('change', function() {
            if (this.value === 'none') {
                defectCountInput.value = '0';
                defectCountInput.readOnly = true;
            } else {
                defectCountInput.readOnly = false;
                if (defectCountInput.value === '0') {
                    defectCountInput.value = '1';
                }
            }
        });
    }

    // Real-time form validation feedback
    const inputs = document.querySelectorAll('.form-control, .form-select');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.checkValidity()) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
    });

    // Confirm dialogs for destructive actions
    const deleteButtons = document.querySelectorAll('[data-action="delete"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                event.preventDefault();
            }
        });
    });

    // Auto-refresh dashboard data every 30 seconds
    if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
        setInterval(refreshDashboardData, 30000);
    }

    // Loading states for form submissions
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(button => {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            if (form && form.checkValidity()) {
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = this.dataset.originalText || 'Submit';
                }, 5000);
            }
        });
        
        // Store original text
        button.dataset.originalText = button.innerHTML;
    });
});

// Utility functions
function refreshDashboardData() {
    fetch('/api/dashboard/kpis')
        .then(response => response.json())
        .then(data => {
            // Update KPI cards
            updateKPICard('total-batches', data.production.total_batches || 0);
            updateKPICard('total-tests', data.quality.total_tests || 0);
            updateKPICard('total-energy', (data.energy.total_consumption || 0).toFixed(1));
            updateKPICard('total-waste', (data.waste.total_waste || 0).toFixed(1));
        })
        .catch(error => console.log('Dashboard refresh failed:', error));
}

function updateKPICard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
        
        // Add a brief highlight animation
        element.classList.add('text-success');
        setTimeout(() => {
            element.classList.remove('text-success');
        }, 1000);
    }
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

function formatNumber(num, decimals = 1) {
    return Number(num).toFixed(decimals);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatCurrency(amount, currency = 'MAD') {
    return `${formatNumber(amount, 2)} ${currency}`;
}

// Export functions for global use
window.DersaEQ = {
    refreshDashboardData,
    updateKPICard,
    showNotification,
    formatNumber,
    formatDate,
    formatCurrency
};