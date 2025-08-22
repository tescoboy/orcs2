// Admin Dashboard - Main JavaScript for tenant management

let tenantService;
let currentEditTenantId = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    tenantService = new TenantService();
    loadTenants();
    setupEventListeners();
});

function setupEventListeners() {
    // Modal event listeners
    const tenantModal = document.getElementById('tenantModal');
    tenantModal.addEventListener('hidden.bs.modal', function() {
        resetForm();
    });

    // Form submission
    document.getElementById('tenantForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveTenant();
    });
}

async function loadTenants() {
    try {
        const tenants = await tenantService.getAllTenants();
        displayTenants(tenants);
    } catch (error) {
        console.error('Failed to load tenants:', error);
    }
}

function displayTenants(tenants) {
    const tbody = document.getElementById('tenantsTableBody');
    tbody.innerHTML = '';

    if (tenants.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    No tenants found. Create your first tenant to get started.
                </td>
            </tr>
        `;
        return;
    }

    tenants.forEach(tenant => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><code>${tenant.id}</code></td>
            <td>${tenant.name}</td>
            <td>${tenant.subdomain}</td>
            <td>${tenantService.getStatusBadge(tenant.status || 'active')}</td>
            <td>${tenantService.formatDate(tenant.created_at)}</td>
            <td class="tenant-actions">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editTenant('${tenant.id}')">
                        Edit
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteTenant('${tenant.id}')">
                        Delete
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function openCreateTenantModal() {
    currentEditTenantId = null;
    document.getElementById('modalTitle').textContent = 'Create New Tenant';
    document.getElementById('tenantForm').reset();
    document.getElementById('maxDailyBudget').value = '10000';
    
    const modal = new bootstrap.Modal(document.getElementById('tenantModal'));
    modal.show();
}

async function editTenant(tenantId) {
    try {
        const tenant = await tenantService.getTenantById(tenantId);
        if (!tenant) return;

        currentEditTenantId = tenantId;
        document.getElementById('modalTitle').textContent = 'Edit Tenant';
        
        // Populate form fields
        document.getElementById('tenantName').value = tenant.name;
        document.getElementById('subdomain').value = tenant.subdomain;
        document.getElementById('billingPlan').value = tenant.billing_plan || 'standard';
        document.getElementById('maxDailyBudget').value = tenant.max_daily_budget || 10000;

        const modal = new bootstrap.Modal(document.getElementById('tenantModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading tenant for edit:', error);
    }
}

async function saveTenant() {
    const formData = {
        name: document.getElementById('tenantName').value,
        subdomain: document.getElementById('subdomain').value,
        billing_plan: document.getElementById('billingPlan').value,
        max_daily_budget: parseInt(document.getElementById('maxDailyBudget').value)
    };

    try {
        if (currentEditTenantId) {
            await tenantService.updateTenant(currentEditTenantId, formData);
        } else {
            await tenantService.createTenant(formData);
        }

        // Close modal and refresh list
        const modal = bootstrap.Modal.getInstance(document.getElementById('tenantModal'));
        modal.hide();
        await loadTenants();
    } catch (error) {
        console.error('Error saving tenant:', error);
    }
}

async function deleteTenant(tenantId) {
    if (!confirm('Are you sure you want to delete this tenant? This action cannot be undone.')) {
        return;
    }

    try {
        await tenantService.deleteTenant(tenantId);
        await loadTenants();
    } catch (error) {
        console.error('Error deleting tenant:', error);
    }
}

function resetForm() {
    currentEditTenantId = null;
    document.getElementById('tenantForm').reset();
    document.getElementById('maxDailyBudget').value = '10000';
}

// Utility functions
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Loading...';
    }
}

function hideLoading(elementId, originalText) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = originalText;
    }
}
