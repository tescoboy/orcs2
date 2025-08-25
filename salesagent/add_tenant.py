#!/usr/bin/env python3

import os
import sys
import secrets
import string
from datetime import datetime, timezone

# Set the database URL
os.environ['DATABASE_URL'] = 'sqlite:///./adcp.db'

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant

def add_tenant():
    """Add a new tenant to the database."""
    
    print("🏢 Add New Publisher Tenant")
    print("=" * 40)
    
    # Get tenant details
    tenant_name = input("Enter publisher name (e.g., 'The New York Times'): ").strip()
    if not tenant_name:
        print("❌ Publisher name is required!")
        return
    
    subdomain = input(f"Enter subdomain (leave blank to auto-generate): ").strip()
    if not subdomain:
        subdomain = tenant_name.lower().replace(" ", "_").replace("-", "_")
        subdomain = "".join(c for c in subdomain if c.isalnum() or c == "_")
        print(f"📝 Auto-generated subdomain: {subdomain}")
    
    tenant_id = input(f"Enter tenant ID (leave blank to use '{subdomain}'): ").strip()
    if not tenant_id:
        tenant_id = subdomain
    
    # Choose ad server
    print("\nSelect ad server:")
    print("1. Mock (for testing)")
    print("2. Google Ad Manager") 
    print("3. Kevel")
    print("4. Other")
    
    ad_server_choice = input("Enter choice (1-4): ").strip()
    ad_server_map = {
        "1": "mock",
        "2": "google_ad_manager", 
        "3": "kevel",
        "4": "other"
    }
    ad_server = ad_server_map.get(ad_server_choice, "mock")
    
    # Generate admin token
    admin_token = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    print(f"\n📋 Publisher Details:")
    print(f"Name: {tenant_name}")
    print(f"Tenant ID: {tenant_id}")
    print(f"Subdomain: {subdomain}")
    print(f"Ad Server: {ad_server}")
    print(f"Admin Token: {admin_token}")
    
    confirm = input("\n✅ Create this publisher? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return
    
    try:
        with get_db_session() as db_session:
            # Check if tenant already exists
            existing = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if existing:
                print(f"❌ Tenant with ID {tenant_id} already exists!")
                return
            
            # Create new tenant
            new_tenant = Tenant(
                tenant_id=tenant_id,
                name=tenant_name,
                subdomain=subdomain,
                is_active=True,
                ad_server=ad_server,
                max_daily_budget=10000,
                enable_aee_signals=True,
                authorized_emails='["admin@example.com"]',
                authorized_domains='["example.com"]',
                admin_token=admin_token,
                human_review_required=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            db_session.add(new_tenant)
            db_session.commit()
            
            print(f"\n🎉 Publisher '{tenant_name}' created successfully!")
            print(f"🌐 Access URL: http://localhost:8000/tenant/{tenant_id}/login")
            print(f"🔑 Admin Token: {admin_token}")
            print(f"📊 Admin Dashboard: http://localhost:8000/tenant/{tenant_id}/")
            
    except Exception as e:
        print(f"❌ Error creating publisher: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_tenant()
