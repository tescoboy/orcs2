#!/usr/bin/env python3
"""Simple database test."""

import sqlite3
import json

def main():
    db_path = "/Users/harvingupta/.adcp/adcp.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tenants
        cursor.execute("SELECT tenant_id, name FROM tenants WHERE is_active = 1")
        tenants = cursor.fetchall()
        print(f"Found {len(tenants)} active tenants:")
        for tenant_id, name in tenants:
            print(f"  - {tenant_id}: {name}")
        
        # Check products for first tenant
        if tenants:
            tenant_id = tenants[0][0]
            cursor.execute("SELECT product_id, name, description FROM products WHERE tenant_id = ? LIMIT 5", (tenant_id,))
            products = cursor.fetchall()
            print(f"\nFound {len(products)} products for tenant {tenant_id}:")
            for product_id, name, description in products:
                print(f"  - {product_id}: {name}")
                print(f"    Description: {description[:100]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
