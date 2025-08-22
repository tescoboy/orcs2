// Tenant Service - API operations for tenant management

class TenantService {
    constructor() {
        this.baseUrl = '/api/tenants';
        this.tenants = [];
    }

    async getAllTenants() {
        try {
            const response = await fetch(this.baseUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.tenants = await response.json();
            return this.tenants;
        } catch (error) {
            console.error('Error fetching tenants:', error);
            this.showAlert('Error loading tenants', 'danger');
            return [];
        }
    }

    async createTenant(tenantData) {
        try {
            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(tenantData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const newTenant = await response.json();
            this.tenants.push(newTenant);
            this.showAlert('Tenant created successfully', 'success');
            return newTenant;
        } catch (error) {
            console.error('Error creating tenant:', error);
            this.showAlert('Error creating tenant', 'danger');
            throw error;
        }
    }

    async updateTenant(tenantId, tenantData) {
        try {
            const response = await fetch(`${this.baseUrl}/${tenantId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(tenantData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const updatedTenant = await response.json();
            const index = this.tenants.findIndex(t => t.id === tenantId);
            if (index !== -1) {
                this.tenants[index] = updatedTenant;
            }
            this.showAlert('Tenant updated successfully', 'success');
            return updatedTenant;
        } catch (error) {
            console.error('Error updating tenant:', error);
            this.showAlert('Error updating tenant', 'danger');
            throw error;
        }
    }

    async deleteTenant(tenantId) {
        try {
            const response = await fetch(`${this.baseUrl}/${tenantId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.tenants = this.tenants.filter(t => t.id !== tenantId);
            this.showAlert('Tenant deleted successfully', 'success');
            return true;
        } catch (error) {
            console.error('Error deleting tenant:', error);
            this.showAlert('Error deleting tenant', 'danger');
            throw error;
        }
    }

    async getTenantById(tenantId) {
        try {
            const response = await fetch(`${this.baseUrl}/${tenantId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching tenant:', error);
            this.showAlert('Error loading tenant details', 'danger');
            return null;
        }
    }

    showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer') || this.createAlertContainer();
        const alertId = 'alert-' + Date.now();
        
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    createAlertContainer() {
        const container = document.createElement('div');
        container.id = 'alertContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
        return container;
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString();
    }

    getStatusBadge(status) {
        const statusClass = status === 'active' ? 'success' : 'secondary';
        return `<span class="badge bg-${statusClass} status-badge">${status}</span>`;
    }
}

// Export for use in other files
window.TenantService = TenantService;
