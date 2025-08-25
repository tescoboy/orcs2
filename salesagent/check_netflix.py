#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant

with get_db_session() as db:
    tenants = db.query(Tenant).filter(Tenant.tenant_id.like('%netflix%')).all()
    print(f'Found {len(tenants)} Netflix tenants:')
    for t in tenants:
        print(f'  - {t.tenant_id}: {t.name}, active: {t.is_active}, policy_settings: {bool(t.policy_settings)}')
        if t.policy_settings:
            print(f'    Policy settings: {t.policy_settings}')
