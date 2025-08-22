# AdCP Admin & Publisher Demo System

A demo system for the Advertising Context Protocol (AdCP) featuring admin and publisher interfaces with full CRUD capabilities and bulk CSV upload functionality.

## 🚀 Quick Start

### Prerequisites
- Node.js (version 14 or higher)
- npm (comes with Node.js)

### Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd salesagent

# Install dependencies
npm install

# Start the server
npm start
```

### Access URLs
- **Admin Dashboard:** http://localhost:3000/admin
- **Publisher Login:** http://localhost:3000/publisher
- **API Base:** http://localhost:3000/api

## 📋 Features

### Admin Section
- ✅ Tenant management (Create, Read, Update, Delete)
- ✅ Multi-tenant support
- ✅ Simple demo interface

### Publisher Section
- ✅ Product catalog with full CRUD
- ✅ Bulk CSV upload functionality
- ✅ Product statistics and analytics
- ✅ Demo login (no real authentication)

### Technical Features
- ✅ File-based data persistence
- ✅ Bootstrap CSS styling
- ✅ Mobile responsive design
- ✅ RESTful API endpoints
- ✅ CSV import/export

## 🏗️ Project Structure

```
salesagent/
├── admin/                 # Admin section
│   ├── index.html        # Admin dashboard
│   ├── api-server.js     # Express.js API server
│   ├── admin.js          # Admin JavaScript
│   └── tenant-service.js # Tenant API service
├── publisher/            # Publisher section
│   ├── login.html        # Publisher login
│   ├── dashboard.html    # Publisher dashboard
│   ├── dashboard.js      # Dashboard functionality
│   ├── product-service.js # Product API service
│   └── product-catalog.js # Product CRUD operations
├── styles/               # CSS files
│   ├── admin.css         # Admin styles
│   └── publisher.css     # Publisher styles
├── templates/            # Template files
│   └── product_template.csv # CSV template for bulk upload
├── package.json          # Dependencies and scripts
└── README.md            # This file
```

## 🔧 API Endpoints

### Admin/Tenant Management
- `GET /api/tenants` - List all tenants
- `POST /api/tenants` - Create new tenant
- `PUT /api/tenants/:id` - Update tenant
- `DELETE /api/tenants/:id` - Delete tenant
- `GET /api/tenants/:id` - Get tenant by ID

### Publisher/Product Management
- `GET /api/products` - List all products
- `POST /api/products` - Create new product
- `PUT /api/products/:id` - Update product
- `DELETE /api/products/:id` - Delete product
- `GET /api/products/:id` - Get product by ID
- `POST /api/products/upload` - Bulk upload CSV
- `GET /api/products/stats` - Get product statistics

## 📊 Demo Data

The system starts with:
- **Demo Tenant:** `demo-tenant-1`
- **Demo Products:** Sample products for testing

## 🎯 Usage Examples

### Creating a New Product
1. Login as publisher
2. Navigate to Product Catalog
3. Click "Create Product"
4. Fill in product details
5. Save product

### Bulk Upload Products
1. Download CSV template
2. Fill in product data
3. Upload CSV file
4. Products are automatically imported

### Managing Tenants
1. Access Admin Dashboard
2. View existing tenants
3. Create, edit, or delete tenants

## 🛠️ Development

### Coding Standards
- All files under 150 lines
- Bootstrap CSS only (no inline CSS)
- Simple, readable code
- Mobile responsive design

### Data Persistence
- File-based storage using JSON files
- Data persists across server restarts
- Located in `admin/data/` directory

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Check if server is running
curl http://localhost:3000/api/products

# Kill process if needed
lsof -ti:3000 | xargs kill -9
npm start
```

### CSV Upload Issues
- Ensure CSV format matches template
- Check file extension is .csv
- Verify all required columns are present

## 📝 License

This is a demo system for educational and testing purposes.

## 🤝 Contributing

1. Follow the coding standards (files under 150 lines)
2. Use Bootstrap for styling
3. Keep code simple and readable
4. Test thoroughly before committing

---

**Status:** ✅ Production Ready Demo System
