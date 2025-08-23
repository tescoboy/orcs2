#!/usr/bin/env python3
"""Check existing tenants in the database."""

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant

def main():
    with get_db_session() as session:
        tenants = session.query(Tenant).all()
        print(f"Found {len(tenants)} tenants:")
        for tenant in tenants:
            print(f"- {tenant.id}: {tenant.name} (slug: {tenant.slug})")
        
        if not tenants:
            print("No tenants found. You may need to create a default tenant.")

if __name__ == "__main__":
    main()
