// Publisher Dashboard - Main functionality

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    const sessionData = localStorage.getItem('publisherSession');
    if (!sessionData) {
        console.log('No session found, redirecting to login');
        window.location.href = 'login.html';
        return;
    }

    try {
        const session = JSON.parse(sessionData);
        
        // Validate session data
        if (!session.tenantId || session.tenantId === 'undefined' || session.tenantId === '') {
            console.error('Invalid session: missing or invalid tenant ID');
            localStorage.removeItem('publisherSession');
            alert('Session is invalid. Please log in again.');
            window.location.href = 'login.html';
            return;
        }
        
        if (!session.publisherName) {
            console.error('Invalid session: missing publisher name');
            localStorage.removeItem('publisherSession');
            alert('Session is invalid. Please log in again.');
            window.location.href = 'login.html';
            return;
        }
        
        console.log('Valid session found:', session);
        document.getElementById('publisherName').textContent = session.publisherName;
        
        // Initialize product service
        if (window.initializeProductService) {
            window.initializeProductService();
        }
        
        // Load initial dashboard stats
        loadDashboardStats();
        
        // Show dashboard by default
        showDashboard();
    } catch (error) {
        console.error('Error loading dashboard:', error);
        localStorage.removeItem('publisherSession');
        alert('Session data is corrupted. Please log in again.');
        window.location.href = 'login.html';
    }
});

function showDashboard() {
    document.getElementById('dashboardContent').style.display = 'block';
    document.getElementById('productCatalogContent').style.display = 'none';
    document.getElementById('csvUploadContent').style.display = 'none';
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.querySelector('.nav-link[onclick="showDashboard()"]').classList.add('active');
    
    loadDashboardStats();
}

function showProductCatalog() {
    document.getElementById('dashboardContent').style.display = 'none';
    document.getElementById('productCatalogContent').style.display = 'block';
    document.getElementById('csvUploadContent').style.display = 'none';
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.querySelector('.nav-link[onclick="showProductCatalog()"]').classList.add('active');
    
    // Load products
    if (window.loadProducts) {
        window.loadProducts();
    }
}

function showCSVUpload() {
    document.getElementById('dashboardContent').style.display = 'none';
    document.getElementById('productCatalogContent').style.display = 'none';
    document.getElementById('csvUploadContent').style.display = 'block';
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.querySelector('.nav-link[onclick="showCSVUpload()"]').classList.add('active');
}

function showAnalytics() {
    alert('Analytics feature coming soon!');
}

async function loadDashboardStats() {
    try {
        const sessionData = localStorage.getItem('publisherSession');
        if (sessionData) {
            const session = JSON.parse(sessionData);
            const response = await fetch(`/api/products/stats?tenant_id=${session.tenantId}`);
            const stats = await response.json();
            
            document.getElementById('totalProducts').textContent = stats.total_products || 0;
            document.getElementById('activeProducts').textContent = stats.active_products || 0;
            document.getElementById('totalRevenue').textContent = `$${stats.total_revenue || 0}`;
            document.getElementById('pendingApprovals').textContent = stats.pending_approvals || 0;
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

function logout() {
    localStorage.removeItem('publisherSession');
    window.location.href = 'login.html';
}

// Make functions globally available
window.showDashboard = showDashboard;
window.showProductCatalog = showProductCatalog;
window.showCSVUpload = showCSVUpload;
window.showAnalytics = showAnalytics;
window.logout = logout;
