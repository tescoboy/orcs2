#!/usr/bin/env python3
"""Quick publisher creation script."""

import os, secrets, string
from datetime import datetime, timezone

os.environ['DATABASE_URL'] = 'sqlite:////Users/harvingupta/.adcp/adcp.db'

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant

def add_publisher(name, subdomain=None, ad_server="mock"):
    """Add a publisher quickly."""
    if not subdomain:
        subdomain = name.lower().replace(" ", "_").replace("-", "_")
        subdomain = "".join(c for c in subdomain if c.isalnum() or c == "_")
    
    tenant_id = f"tenant_{subdomain}" if not subdomain.startswith("tenant_") else subdomain
    admin_token = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    try:
        with get_db_session() as db_session:
            existing = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if existing:
                print(f"❌ Tenant {tenant_id} already exists!")
                return False
            
            new_tenant = Tenant(
                tenant_id=tenant_id,
                name=name,
                subdomain=subdomain,
                is_active=True,
                ad_server=ad_server,
                admin_token=admin_token,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            db_session.add(new_tenant)
            db_session.commit()
            
            print(f"✅ Created: {name}")
            print(f"🌐 URL: http://localhost:8000/tenant/{tenant_id}/login")
            print(f"🔑 Token: {admin_token}")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Example usage - modify these:
    add_publisher("The New York Times", "nytimes")
    add_publisher("ESPN", "espn") 
    add_publisher("CNN", "cnn")
