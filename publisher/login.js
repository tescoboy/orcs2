// Publisher Login - Demo authentication

let tenants = [];

document.addEventListener('DOMContentLoaded', function() {
    loadTenants();
    setupEventListeners();
});

function setupEventListeners() {
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', handleLogin);
}

async function loadTenants() {
    try {
        const response = await fetch('/api/tenants');
        if (!response.ok) {
            throw new Error('Failed to load tenants');
        }
        
        tenants = await response.json();
        populateTenantSelect();
    } catch (error) {
        console.error('Error loading tenants:', error);
        showAlert('Error loading tenants. Please refresh the page.', 'danger');
    }
}

function populateTenantSelect() {
    const select = document.getElementById('tenantSelect');
    
    // Clear existing options except the first one
    select.innerHTML = '<option value="">Choose a tenant...</option>';
    
    tenants.forEach(tenant => {
        const option = document.createElement('option');
        option.value = tenant.id;
        option.textContent = `${tenant.name} (${tenant.subdomain})`;
        select.appendChild(option);
    });
}

async function handleLogin(event) {
    event.preventDefault();
    
    const tenantId = document.getElementById('tenantSelect').value;
    
    if (!tenantId) {
        showAlert('Please select a tenant', 'warning');
        return;
    }
    
    // Validate tenant ID is not empty
    if (tenantId.trim() === '') {
        showAlert('Please select a valid tenant', 'warning');
        return;
    }
    
    // Find the selected tenant to get its name
    const selectedTenant = tenants.find(t => t.id === tenantId);
    if (!selectedTenant) {
        showAlert('Selected tenant not found', 'danger');
        return;
    }
    
    // Show loading state
    setLoadingState(true);
    
    try {
        // Store session data (demo mode)
        const sessionData = {
            tenantId: tenantId.trim(),
            publisherName: selectedTenant.name, // Use tenant name as publisher name
            email: 'publisher@adcp.demo', // Hardcoded email
            loginTime: new Date().toISOString()
        };
        
        // Validate session data before storing
        if (!sessionData.tenantId || sessionData.tenantId === '') {
            throw new Error('Invalid tenant ID');
        }
        
        console.log('Creating session with data:', sessionData);
        localStorage.setItem('publisherSession', JSON.stringify(sessionData));
        
        // Verify the session was stored correctly
        const storedSession = localStorage.getItem('publisherSession');
        if (!storedSession) {
            throw new Error('Failed to store session data');
        }
        
        const parsedSession = JSON.parse(storedSession);
        if (!parsedSession.tenantId) {
            throw new Error('Session data is missing tenant ID');
        }
        
        console.log('Session created successfully:', parsedSession);
        
        // Redirect to dashboard
        window.location.href = '/publisher/dashboard.html';
        
    } catch (error) {
        console.error('Login error:', error);
        showAlert(`Login failed: ${error.message}`, 'danger');
        setLoadingState(false);
    }
}

function setLoadingState(isLoading) {
    const btnText = document.getElementById('loginBtnText');
    const btnSpinner = document.getElementById('loginBtnSpinner');
    const submitBtn = document.querySelector('button[type="submit"]');
    
    if (isLoading) {
        btnText.classList.add('d-none');
        btnSpinner.classList.remove('d-none');
        submitBtn.disabled = true;
    } else {
        btnText.classList.remove('d-none');
        btnSpinner.classList.add('d-none');
        submitBtn.disabled = false;
    }
}

function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
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

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.className = 'position-fixed top-0 start-50 translate-middle-x p-3';
    container.style.zIndex = '1050';
    document.body.appendChild(container);
    return container;
}
