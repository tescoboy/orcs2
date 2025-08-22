# Admin Section - Tenant Management

## Overview
This admin section provides a simple interface for managing tenants in the AdCP system. It's designed for demo purposes with no authentication required.

## Features
- **Create Tenants**: Add new publishers to the system
- **View Tenants**: See all tenants in a clean table format
- **Edit Tenants**: Modify tenant details like name, subdomain, and billing plan
- **Delete Tenants**: Remove tenants from the system
- **Bootstrap Styling**: Clean, responsive interface

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Start the Server
```bash
npm start
```

### 3. Access Admin Interface
Open your browser and go to: `http://localhost:3000/admin`

## API Endpoints

### GET /api/tenants
Returns all tenants in the system.

### GET /api/tenants/:id
Returns a specific tenant by ID.

### POST /api/tenants
Creates a new tenant. Required fields:
- `name`: Tenant name
- `subdomain`: Unique subdomain

### PUT /api/tenants/:id
Updates an existing tenant.

### DELETE /api/tenants/:id
Deletes a tenant from the system.

## File Structure
```
admin/
├── index.html          # Main admin dashboard
├── api-server.js       # Express.js API server
├── tenant-service.js   # Frontend API service
├── admin.js           # Main admin JavaScript
└── README.md          # This file

styles/
└── admin.css          # Admin-specific styles
```

## Demo Data
The system comes with one demo tenant:
- **Name**: Demo Publisher 1
- **Subdomain**: demo1
- **Billing Plan**: standard
- **Max Daily Budget**: $10,000

## Development
- All files are kept under 150 lines
- Bootstrap CSS used exclusively
- No inline CSS
- Simple, readable code structure
