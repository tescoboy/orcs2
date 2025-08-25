#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant
import json

def add_netflix_agent():
    """Add a Netflix agent to the Netflix tenant"""
    with get_db_session() as db:
        # Find the Netflix tenant
        netflix_tenant = db.query(Tenant).filter_by(tenant_id='netflix').first()
        
        if not netflix_tenant:
            print("Netflix tenant not found, creating it...")
            netflix_tenant = Tenant(
                tenant_id='netflix',
                name='Netflix',
                is_active=True,
                subdomain='netflix'
            )
            db.add(netflix_tenant)
        
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
        
        print("✅ Added Netflix AI Agent to Netflix tenant")
        print(f"Agent config: {json.dumps(netflix_agent_config, indent=2)}")

if __name__ == "__main__":
    add_netflix_agent()
