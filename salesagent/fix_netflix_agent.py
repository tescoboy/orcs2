#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant
import json

def fix_netflix_agent():
    """Fix the Netflix agent configuration"""
    with get_db_session() as db:
        # Find the Netflix tenant that has products
        netflix_tenant = db.query(Tenant).filter_by(tenant_id='netflix').first()
        
        if not netflix_tenant:
            print("Netflix tenant not found!")
            return
        
        # Create Netflix agent configuration
        netflix_agent_config = {
            "agents": {
                "netflix_ai_agent": {
                    "name": "Netflix AI Agent",
                    "type": "local",
                    "status": "active",
                    "config": {
                        "model": "gemini-1.5-flash",
                        "specialization": "streaming_entertainment"
                    }
                }
            },
            "settings": {
                "default_locale": "en-US",
                "default_currency": "USD"
            }
        }
        
        # Update tenant policy settings
        netflix_tenant.policy_settings = netflix_agent_config
        db.commit()
        
        print("✅ Fixed Netflix AI Agent configuration")
        print(f"Tenant: {netflix_tenant.tenant_id}")
        print(f"Agent config: {json.dumps(netflix_agent_config, indent=2)}")

if __name__ == "__main__":
    fix_netflix_agent()
