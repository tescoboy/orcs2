#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant

with get_db_session() as db:
    tenants = db.query(Tenant).all()
    print('All tenants:')
    for t in tenants:
        print(f'  - {t.tenant_id}: {t.name}')
