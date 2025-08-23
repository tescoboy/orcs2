#!/usr/bin/env python3
"""Check database contents."""

from src.core.database.database_session import get_db_session
from src.core.database.models import Product, Tenant

def main():
    with get_db_session() as session:
        tenants = session.query(Tenant).all()
        products = session.query(Product).all()
        
        print(f"Tenants: {len(tenants)}")
        for tenant in tenants:
            print(f"  - {tenant.tenant_id}: {tenant.name}")
        
        print(f"\nProducts: {len(products)}")
        for product in products[:10]:  # Show first 10
            print(f"  - {product.name} (tenant: {product.tenant_id})")
        
        if len(products) > 10:
            print(f"  ... and {len(products) - 10} more")

if __name__ == "__main__":
    main()
