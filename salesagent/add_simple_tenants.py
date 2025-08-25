#!/usr/bin/env python3

import os
import sys

# Set the database URL
os.environ['DATABASE_URL'] = 'sqlite:///./adcp.db'

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant
from datetime import datetime

def add_simple_tenants():
    sample_tenants = [
        {
            "tenant_id": "netflix",
            "name": "Netflix",
            "subdomain": "netflix-pub",
            "is_active": True,
            "ad_server": "netflix_ad_server",
            "max_daily_budget": 100000,
            "enable_aee_signals": True,
            "authorized_emails": ["admin@netflix.com"],
            "authorized_domains": ["netflix.com"],
            "admin_token": "netflix_admin_token_123",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "tenant_id": "tiktok",
            "name": "TikTok",
            "subdomain": "tiktok-pub",
            "is_active": True,
            "ad_server": "tiktok_ad_server",
            "max_daily_budget": 50000,
            "enable_aee_signals": True,
            "authorized_emails": ["admin@tiktok.com"],
            "authorized_domains": ["tiktok.com"],
            "admin_token": "tiktok_admin_token_123",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "tenant_id": "youtube",
            "name": "YouTube",
            "subdomain": "youtube-pub",
            "is_active": True,
            "ad_server": "youtube_ad_server",
            "max_daily_budget": 75000,
            "enable_aee_signals": True,
            "authorized_emails": ["admin@youtube.com"],
            "authorized_domains": ["youtube.com"],
            "admin_token": "youtube_admin_token_123",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]
    
    with get_db_session() as session:
        for tenant_data in sample_tenants:
            try:
                # Check if tenant already exists
                existing = session.query(Tenant).filter_by(tenant_id=tenant_data["tenant_id"]).first()
                if not existing:
                    tenant = Tenant(**tenant_data)
                    session.add(tenant)
                    session.commit()
                    print(f"Added tenant: {tenant_data['name']}")
                else:
                    print(f"Tenant already exists: {tenant_data['name']}")
            except Exception as e:
                print(f"Error adding {tenant_data['name']}: {e}")
                session.rollback()
        
        print("Tenant addition completed!")

if __name__ == "__main__":
    add_simple_tenants()
