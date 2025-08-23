#!/usr/bin/env python3
"""Test buyer search service directly."""

import os
os.environ['DATABASE_URL'] = 'sqlite:////Users/harvingupta/.adcp/adcp.db'

from services.buyer_search_service import search_products

def main():
    print("Testing buyer search service...")
    
    try:
        # Test search
        products = search_products(
            prompt="display banner",
            max_results=10
        )
        
        print(f"Found {len(products)} products")
        
        for i, product in enumerate(products[:3]):
            print(f"Product {i+1}: {product.get('name')} from {product.get('publisher_name')}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
