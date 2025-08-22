// Product Catalog - CRUD operations and modal management

let productService;
let currentEditProductId = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeProductService();
});

function initializeProductService() {
    const sessionData = localStorage.getItem('publisherSession');
    console.log('Session data from localStorage:', sessionData);
    
    if (sessionData) {
        try {
            const session = JSON.parse(sessionData);
            console.log('Parsed session:', session);
            
            // Validate session has required data
            if (!session.tenantId || session.tenantId === 'undefined' || session.tenantId === '') {
                console.error('Invalid session: missing or invalid tenant ID');
                alert('Session is invalid. Please log in again.');
                window.location.href = 'login.html';
                return;
            }
            
            productService = new ProductService(session.tenantId);
            console.log('Product service initialized for tenant:', session.tenantId);
        } catch (error) {
            console.error('Error initializing product service:', error);
            alert('Error initializing product service. Please log in again.');
            window.location.href = 'login.html';
        }
    } else {
        console.warn('No publisher session found');
        alert('No session found. Please log in.');
        window.location.href = 'login.html';
    }
}

async function loadProducts() {
    if (!productService) {
        console.error('Product service not initialized');
        return;
    }
    
    try {
        const products = await productService.getAllProducts();
        displayProducts(products);
    } catch (error) {
        console.error('Failed to load products:', error);
        displayProducts([]);
    }
}

function displayProducts(products) {
    const tbody = document.getElementById('productsTableBody');
    if (!tbody) {
        console.error('Products table body not found');
        return;
    }
    
    tbody.innerHTML = '';

    if (products.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-4">
                    No products found. Create your first product to get started.
                </td>
            </tr>
        `;
        return;
    }

    products.forEach(product => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><code>${product.product_id}</code></td>
            <td>${product.name}</td>
            <td>${product.description || '-'}</td>
            <td><span class="badge bg-secondary">${product.type}</span></td>
            <td>${productService.formatPrice(product.price)}</td>
            <td>${productService.getStatusBadge(product.status)}</td>
            <td class="product-actions">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editProduct('${product.product_id}')">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteProduct('${product.product_id}')">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function openCreateProductModal() {
    if (!productService) {
        alert('Please log in first to access product management');
        return;
    }
    
    currentEditProductId = null;
    document.getElementById('productModalTitle').textContent = 'Create New Product';
    document.getElementById('productForm').reset();
    
    // Clear any validation states
    clearValidationStates();
    
    const modal = new bootstrap.Modal(document.getElementById('productModal'));
    modal.show();
}

async function editProduct(productId) {
    if (!productService) {
        alert('Please log in first to access product management');
        return;
    }
    
    try {
        const product = await productService.getProductById(productId);
        if (!product) {
            alert('Product not found');
            return;
        }

        currentEditProductId = productId;
        document.getElementById('productModalTitle').textContent = 'Edit Product';
        
        // Populate form fields
        document.getElementById('productName').value = product.name;
        document.getElementById('productType').value = product.type;
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productPrice').value = product.price;
        document.getElementById('productStatus').value = product.status;
        document.getElementById('productId').value = product.product_id;

        // Set targeting options
        const targetingOptions = product.targeting_options || [];
        document.getElementById('targetingGeo').checked = targetingOptions.includes('geo');
        document.getElementById('targetingDemo').checked = targetingOptions.includes('demo');
        document.getElementById('targetingInterests').checked = targetingOptions.includes('interests');

        const modal = new bootstrap.Modal(document.getElementById('productModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading product for edit:', error);
        alert('Error loading product details');
    }
}

async function saveProduct() {
    if (!productService) {
        alert('Please log in first to access product management');
        return;
    }
    
    // Validate form
    if (!validateProductForm()) {
        return;
    }
    
    // Collect form data
    const formData = {
        name: document.getElementById('productName').value,
        type: document.getElementById('productType').value,
        description: document.getElementById('productDescription').value,
        price: parseFloat(document.getElementById('productPrice').value),
        status: document.getElementById('productStatus').value,
        targeting_options: getTargetingOptions()
    };

    // Show loading state
    setSaveButtonLoading(true);

    try {
        if (currentEditProductId) {
            await productService.updateProduct(currentEditProductId, formData);
        } else {
            await productService.createProduct(formData);
        }

        // Close modal and refresh list
        const modal = bootstrap.Modal.getInstance(document.getElementById('productModal'));
        modal.hide();
        await loadProducts();
    } catch (error) {
        console.error('Error saving product:', error);
        alert('Error saving product. Please try again.');
    } finally {
        setSaveButtonLoading(false);
    }
}

async function deleteProduct(productId) {
    if (!productService) {
        alert('Please log in first to access product management');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this product? This action cannot be undone.')) {
        return;
    }

    try {
        await productService.deleteProduct(productId);
        await loadProducts();
    } catch (error) {
        console.error('Error deleting product:', error);
        alert('Error deleting product. Please try again.');
    }
}

async function deleteAllProducts() {
    if (!productService) {
        alert('Please log in first to access product management');
        return;
    }
    
    const products = await productService.getAllProducts();
    if (products.length === 0) {
        alert('No products to delete');
        return;
    }
    
    const confirmMessage = `Are you sure you want to delete ALL ${products.length} products? This action cannot be undone.`;
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        // Delete all products one by one
        for (const product of products) {
            await productService.deleteProduct(product.product_id);
        }
        
        // Refresh the product list
        await loadProducts();
        
        alert(`Successfully deleted ${products.length} products`);
    } catch (error) {
        console.error('Error deleting all products:', error);
        alert('Error deleting products. Please try again.');
    }
}

function validateProductForm() {
    let isValid = true;
    clearValidationStates();

    // Validate required fields
    const requiredFields = ['productName', 'productType', 'productPrice'];
    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        }
    });

    // Validate price
    const priceField = document.getElementById('productPrice');
    if (priceField.value && (isNaN(parseFloat(priceField.value)) || parseFloat(priceField.value) < 0)) {
        priceField.classList.add('is-invalid');
        isValid = false;
    }

    return isValid;
}

function clearValidationStates() {
    const form = document.getElementById('productForm');
    if (form) {
        form.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
    }
}

function getTargetingOptions() {
    const options = [];
    if (document.getElementById('targetingGeo').checked) options.push('geo');
    if (document.getElementById('targetingDemo').checked) options.push('demo');
    if (document.getElementById('targetingInterests').checked) options.push('interests');
    return options;
}

function setSaveButtonLoading(isLoading) {
    const btnText = document.getElementById('saveBtnText');
    const btnSpinner = document.getElementById('saveBtnSpinner');
    const saveBtn = document.querySelector('#productModal .btn-primary');
    
    if (isLoading) {
        btnText.classList.add('d-none');
        btnSpinner.classList.remove('d-none');
        saveBtn.disabled = true;
    } else {
        btnText.classList.remove('d-none');
        btnSpinner.classList.add('d-none');
        saveBtn.disabled = false;
    }
}

// CSV Upload functionality
async function handleCSVUpload(event) {
    event.preventDefault();
    
    if (!productService) {
        alert('Please log in first to access bulk upload');
        return;
    }
    
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a CSV file');
        return;
    }
    
    if (!file.name.endsWith('.csv')) {
        alert('Please select a valid CSV file');
        return;
    }
    
    try {
        const result = await productService.uploadCSV(file);
        console.log('CSV upload result:', result);
        
        // Refresh product list
        await loadProducts();
        
        // Clear file input
        fileInput.value = '';
        
        alert(`Successfully uploaded ${result.imported_count} products!`);
        
    } catch (error) {
        console.error('CSV upload error:', error);
        alert('Error uploading CSV file. Please try again.');
    }
}

// Make functions globally available
window.loadProducts = loadProducts;
window.openCreateProductModal = openCreateProductModal;
window.editProduct = editProduct;
window.saveProduct = saveProduct;
window.deleteProduct = deleteProduct;
window.deleteAllProducts = deleteAllProducts;
window.handleCSVUpload = handleCSVUpload;
window.initializeProductService = initializeProductService;
