#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Product

with get_db_session() as db:
    # Search for crime-related products
    crime_products = db.query(Product).filter(Product.name.like('%crime%')).all()
    print(f'Found {len(crime_products)} crime-related products:')
    for p in crime_products:
        print(f'  - {p.name}: {p.description[:50]}... (tenant: {p.tenant_id})')
    
    print("\n" + "="*50)
    
    # Search for products with "true" in the name
    true_products = db.query(Product).filter(Product.name.like('%true%')).all()
    print(f'Found {len(true_products)} products with "true" in name:')
    for p in true_products:
        print(f'  - {p.name}: {p.description[:50]}... (tenant: {p.tenant_id})')
    
    print("\n" + "="*50)
    
    # Search for recent products (last 10)
    recent_products = db.query(Product).order_by(Product.product_id.desc()).limit(10).all()
    print(f'Found {len(recent_products)} recent products:')
    for p in recent_products:
        print(f'  - {p.name}: {p.description[:50]}... (tenant: {p.tenant_id})')
