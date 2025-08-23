#!/usr/bin/env python3
"""Test database connectivity."""

import os
os.environ['DATABASE_URL'] = 'sqlite:///./adcp.db'

from src.core.database.db_config import DatabaseConfig
from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant

def main():
    print("Testing database connectivity...")
    print(f"Database URL: {DatabaseConfig.get_connection_string()}")
    
    try:
        with get_db_session() as session:
            tenants = session.query(Tenant).all()
            print(f"✅ Successfully connected! Found {len(tenants)} tenants:")
            for tenant in tenants:
                print(f"  - {tenant.tenant_id}: {tenant.name}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    main()
