#!/usr/bin/env python3
import os
os.environ["DATABASE_URL"] = "sqlite:///./adcp.db"
from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant

def test_auth_db_access():
    print("Testing auth blueprint database access...")
    try:
        with get_db_session() as session:
            tenant = session.query(Tenant).filter_by(tenant_id="default").first()
            if tenant:
                print(f"✅ Auth can access database! Found tenant: {tenant.name}")
                return True
            else:
                print("❌ Tenant default not found")
                return False
    except Exception as e:
        print(f"❌ Auth database access failed: {e}")
        return False

if __name__ == "__main__":
    test_auth_db_access()
