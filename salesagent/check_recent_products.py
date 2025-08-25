#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Product

with get_db_session() as db:
    # Get the 10 most recent products
    recent_products = db.query(Product).order_by(Product.product_id.desc()).limit(10).all()
    print('Most recent products:')
    for p in recent_products:
        print(f'  - {p.name} (tenant: {p.tenant_id})')
        print(f'    Description: {p.description[:80]}...')
        print()
