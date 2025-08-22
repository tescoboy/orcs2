// Simple API server for tenant and product management (demo purposes)

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const multer = require('multer');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '..')));

// File paths for data persistence
const TENANTS_FILE = path.join(__dirname, 'data', 'tenants.json');
const PRODUCTS_FILE = path.join(__dirname, 'data', 'products.json');

// Ensure data directory exists
const dataDir = path.dirname(TENANTS_FILE);
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
}

// Load data from files
function loadData() {
    let tenants = [];
    let products = [];
    
    try {
        if (fs.existsSync(TENANTS_FILE)) {
            tenants = JSON.parse(fs.readFileSync(TENANTS_FILE, 'utf8'));
        }
    } catch (error) {
        console.error('Error loading tenants:', error);
    }
    
    try {
        if (fs.existsSync(PRODUCTS_FILE)) {
            products = JSON.parse(fs.readFileSync(PRODUCTS_FILE, 'utf8'));
        }
    } catch (error) {
        console.error('Error loading products:', error);
    }
    
    return { tenants, products };
}

// Save data to files
function saveData(tenants, products) {
    try {
        fs.writeFileSync(TENANTS_FILE, JSON.stringify(tenants, null, 2));
        fs.writeFileSync(PRODUCTS_FILE, JSON.stringify(products, null, 2));
    } catch (error) {
        console.error('Error saving data:', error);
    }
}

// Initialize data
let { tenants, products } = loadData();

// Add demo data if no data exists
if (tenants.length === 0) {
    tenants = [
        {
            id: 'demo-tenant-1',
            name: 'Demo Publisher 1',
            subdomain: 'demo1',
            billing_plan: 'standard',
            max_daily_budget: 10000,
            status: 'active',
            created_at: new Date().toISOString()
        }
    ];
}

if (products.length === 0) {
    products = [
        {
            product_id: 'prod-1',
            tenant_id: 'demo-tenant-1',
            name: 'Premium Video Ad',
            description: 'High-quality video advertising slot',
            type: 'video',
            price: 25,
            status: 'active',
            targeting_options: ['geo', 'demo', 'interests'],
            created_at: new Date().toISOString()
        }
    ];
}

// Save initial data
saveData(tenants, products);

// Tenant Management Routes
app.get('/api/tenants', (req, res) => {
    res.json(tenants);
});

app.post('/api/tenants', (req, res) => {
    const newTenant = {
        id: `tenant-${Date.now()}`,
        ...req.body,
        created_at: new Date().toISOString()
    };
    
    tenants.push(newTenant);
    saveData(tenants, products);
    res.status(201).json(newTenant);
});

app.put('/api/tenants/:id', (req, res) => {
    const index = tenants.findIndex(t => t.id === req.params.id);
    if (index === -1) {
        return res.status(404).json({ error: 'Tenant not found' });
    }
    
    tenants[index] = { ...tenants[index], ...req.body };
    saveData(tenants, products);
    res.json(tenants[index]);
});

app.delete('/api/tenants/:id', (req, res) => {
    const index = tenants.findIndex(t => t.id === req.params.id);
    if (index === -1) {
        return res.status(404).json({ error: 'Tenant not found' });
    }
    
    tenants.splice(index, 1);
    saveData(tenants, products);
    res.status(204).send();
});

app.get('/api/tenants/:id', (req, res) => {
    const tenant = tenants.find(t => t.id === req.params.id);
    if (!tenant) {
        return res.status(404).json({ error: 'Tenant not found' });
    }
    res.json(tenant);
});

// Product Management Routes
app.get('/api/products', (req, res) => {
    const { tenant_id } = req.query;
    
    if (tenant_id) {
        // Filter products by tenant
        const filteredProducts = products.filter(p => p.tenant_id === tenant_id);
        res.json(filteredProducts);
    } else {
        // Return all products
        res.json(products);
    }
});

app.post('/api/products', (req, res) => {
    const newProduct = {
        product_id: req.body.product_id || `prod-${Date.now()}`,
        tenant_id: req.body.tenant_id || 'demo-tenant-1',
        ...req.body,
        created_at: new Date().toISOString()
    };
    
    products.push(newProduct);
    saveData(tenants, products);
    res.status(201).json(newProduct);
});

app.put('/api/products/:id', (req, res) => {
    const index = products.findIndex(p => p.product_id === req.params.id);
    if (index === -1) {
        return res.status(404).json({ error: 'Product not found' });
    }
    
    products[index] = { ...products[index], ...req.body };
    saveData(tenants, products);
    res.json(products[index]);
});

app.delete('/api/products/:id', (req, res) => {
    const index = products.findIndex(p => p.product_id === req.params.id);
    if (index === -1) {
        return res.status(404).json({ error: 'Product not found' });
    }
    
    products.splice(index, 1);
    saveData(tenants, products);
    res.status(204).send();
});

app.get('/api/products/:id', (req, res) => {
    const product = products.find(p => p.product_id === req.params.id);
    if (!product) {
        return res.status(404).json({ error: 'Product not found' });
    }
    res.json(product);
});

// Product Statistics
app.get('/api/products/stats', (req, res) => {
    const { tenant_id } = req.query;
    
    let filteredProducts = products;
    if (tenant_id) {
        filteredProducts = products.filter(p => p.tenant_id === tenant_id);
    }
    
    const total_products = filteredProducts.length;
    const active_products = filteredProducts.filter(p => p.status === 'active').length;
    const total_revenue = filteredProducts.reduce((sum, p) => sum + (p.price || 0), 0);
    const pending_approvals = filteredProducts.filter(p => p.status === 'draft').length;
    
    res.json({
        total_products,
        active_products,
        total_revenue,
        pending_approvals
    });
});

// CSV Upload
const upload = multer({ dest: 'uploads/' });

app.post('/api/products/upload', upload.single('csv'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
    }
    
    // Get tenant_id from form data
    const tenant_id = req.body.tenant_id;
    if (!tenant_id) {
        return res.status(400).json({ error: 'No tenant_id provided' });
    }
    
    console.log('CSV upload for tenant:', tenant_id);
    
    try {
        const csvContent = fs.readFileSync(req.file.path, 'utf8');
        const lines = csvContent.split('\n').filter(line => line.trim()); // Remove empty lines
        
        if (lines.length < 2) {
            return res.status(400).json({ error: 'CSV file must have at least a header and one data row' });
        }
        
        const headers = lines[0].split(',').map(h => h.trim());
        console.log('CSV Headers:', headers);
        
        let imported_count = 0;
        
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;
            
            // Handle CSV parsing with quotes
            const values = [];
            let current = '';
            let inQuotes = false;
            
            for (let j = 0; j < line.length; j++) {
                const char = line[j];
                if (char === '"') {
                    inQuotes = !inQuotes;
                } else if (char === ',' && !inQuotes) {
                    values.push(current.trim());
                    current = '';
                } else {
                    current += char;
                }
            }
            values.push(current.trim()); // Add the last value
            
            console.log(`Row ${i} values:`, values);
            
            // Parse targeting options
            let targeting_options = [];
            const targetingIndex = headers.indexOf('targeting_options');
            if (targetingIndex >= 0 && values[targetingIndex]) {
                const targetingStr = values[targetingIndex].replace(/"/g, '');
                targeting_options = targetingStr.split(',').map(opt => opt.trim()).filter(opt => opt);
            }
            
            const product = {
                product_id: values[headers.indexOf('product_id')] || `prod-${Date.now()}-${i}`,
                tenant_id: tenant_id, // Use tenant_id from form data
                name: values[headers.indexOf('name')] || '',
                description: values[headers.indexOf('description')] || '',
                type: values[headers.indexOf('type')] || 'display',
                price: parseFloat(values[headers.indexOf('price')]) || 0,
                status: 'active', // Default to active
                targeting_options: targeting_options,
                created_at: new Date().toISOString()
            };
            
            console.log('Created product:', product);
            products.push(product);
            imported_count++;
        }
        
        // Clean up uploaded file
        fs.unlinkSync(req.file.path);
        
        // Save data immediately
        saveData(tenants, products);
        
        console.log(`CSV upload completed. Imported ${imported_count} products. Total products: ${products.length}`);
        res.json({ 
            success: true, 
            imported_count, 
            total_products: products.length,
            tenant_id: tenant_id
        });
        
    } catch (error) {
        console.error('CSV upload error:', error);
        
        // Clean up uploaded file if it exists
        if (req.file && fs.existsSync(req.file.path)) {
            fs.unlinkSync(req.file.path);
        }
        
        res.status(500).json({ error: 'Failed to process CSV file: ' + error.message });
    }
});

// Static file routes
app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.get('/publisher', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'publisher', 'login.html'));
});

// Start server
app.listen(PORT, () => {
    console.log(`API server running on http://localhost:${PORT}`);
    console.log(`Admin interface: http://localhost:${PORT}/admin`);
    console.log(`Publisher login: http://localhost:${PORT}/publisher`);
});

module.exports = app;
