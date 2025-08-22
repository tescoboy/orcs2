// Product Service - API operations for product management

class ProductService {
    constructor(tenantId) {
        this.baseUrl = `/api/products`;
        this.tenantId = tenantId;
        this.products = [];
    }

    async getAllProducts() {
        try {
            const response = await fetch(`${this.baseUrl}?tenant_id=${this.tenantId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.products = await response.json();
            return this.products;
        } catch (error) {
            console.error('Error fetching products:', error);
            this.showAlert('Error loading products', 'danger');
            return [];
        }
    }

    async createProduct(productData) {
        try {
            const response = await fetch(this.baseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ...productData,
                    tenant_id: this.tenantId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const newProduct = await response.json();
            this.products.push(newProduct);
            this.showAlert('Product created successfully', 'success');
            return newProduct;
        } catch (error) {
            console.error('Error creating product:', error);
            this.showAlert('Error creating product', 'danger');
            throw error;
        }
    }

    async updateProduct(productId, productData) {
        try {
            const response = await fetch(`${this.baseUrl}/${productId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(productData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const updatedProduct = await response.json();
            const index = this.products.findIndex(p => p.product_id === productId);
            if (index !== -1) {
                this.products[index] = updatedProduct;
            }
            this.showAlert('Product updated successfully', 'success');
            return updatedProduct;
        } catch (error) {
            console.error('Error updating product:', error);
            this.showAlert('Error updating product', 'danger');
            throw error;
        }
    }

    async deleteProduct(productId) {
        try {
            const response = await fetch(`${this.baseUrl}/${productId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.products = this.products.filter(p => p.product_id !== productId);
            this.showAlert('Product deleted successfully', 'success');
            return true;
        } catch (error) {
            console.error('Error deleting product:', error);
            this.showAlert('Error deleting product', 'danger');
            throw error;
        }
    }

    async getProductById(productId) {
        try {
            const response = await fetch(`${this.baseUrl}/${productId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching product:', error);
            this.showAlert('Error loading product details', 'danger');
            return null;
        }
    }

    async uploadCSV(file) {
        try {
            const formData = new FormData();
            formData.append('csv', file);
            
            // Get current tenant ID from session
            const sessionData = localStorage.getItem('publisherSession');
            if (!sessionData) {
                throw new Error('No session found. Please log in again.');
            }
            
            const session = JSON.parse(sessionData);
            if (!session.tenantId) {
                throw new Error('No tenant ID found in session. Please log in again.');
            }
            
            // Add tenant ID to form data
            formData.append('tenant_id', session.tenantId);
            
            console.log('Uploading CSV for tenant:', session.tenantId);

            const response = await fetch(`${this.baseUrl}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('CSV upload result:', result);
            this.showAlert(`Successfully uploaded ${result.imported_count} products`, 'success');
            return result;
        } catch (error) {
            console.error('Error uploading CSV:', error);
            this.showAlert(`Error uploading CSV file: ${error.message}`, 'danger');
            throw error;
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

    formatPrice(price) {
        return `$${parseFloat(price).toFixed(2)}`;
    }

    getStatusBadge(status) {
        const statusClass = status === 'active' ? 'success' : 'secondary';
        return `<span class="badge bg-${statusClass}">${status}</span>`;
    }

    validateProductData(data) {
        const errors = [];
        
        if (!data.name || data.name.trim().length === 0) {
            errors.push('Product name is required');
        }
        
        if (!data.type || data.type.trim().length === 0) {
            errors.push('Product type is required');
        }
        
        if (!data.price || isNaN(parseFloat(data.price))) {
            errors.push('Valid price is required');
        }
        
        return errors;
    }
}

// Export for use in other files
window.ProductService = ProductService;
