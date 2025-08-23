#!/usr/bin/env python3
"""Debug script to see what products are in the database."""

import sqlite3
import json

def main():
    db_path = "/Users/harvingupta/.adcp/adcp.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get a few products from each tenant
        cursor.execute("""
            SELECT tenant_id, product_id, name, description, formats, cpm, delivery_type, countries
            FROM products 
            LIMIT 10
        """)
        
        products = cursor.fetchall()
        print(f"Found {len(products)} products in database:")
        print("=" * 80)
        
        for tenant_id, product_id, name, description, formats_json, cpm, delivery_type, countries_json in products:
            print(f"Tenant: {tenant_id}")
            print(f"Product ID: {product_id}")
            print(f"Name: {name}")
            print(f"Description: {description[:100]}...")
            print(f"CPM: {cpm}")
            print(f"Delivery Type: {delivery_type}")
            
            # Parse JSON fields
            try:
                formats = json.loads(formats_json) if formats_json else []
                print(f"Formats: {formats}")
            except:
                print(f"Formats (raw): {formats_json}")
            
            try:
                countries = json.loads(countries_json) if countries_json else []
                print(f"Countries: {countries}")
            except:
                print(f"Countries (raw): {countries_json}")
            
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
