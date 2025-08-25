#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Product

with get_db_session() as db:
    products = db.query(Product).all()
    print(f'Found {len(products)} products:')
    for p in products:
        print(f'  - {p.name}: {p.description[:50]}...')
        print(f'    Tenant: {p.tenant_id}, CPM: ${p.cpm}')
