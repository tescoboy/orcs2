#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant
import json

def merge_netflix_agent():
    """Merge Netflix agent configuration into existing policy settings"""
    with get_db_session() as db:
        netflix_tenant = db.query(Tenant).filter_by(tenant_id='netflix').first()
        
        if not netflix_tenant:
            print("Netflix tenant not found!")
            return
        
        # Get existing policy settings
        existing_settings = netflix_tenant.policy_settings or {}
        
        # Add agent configuration
        existing_settings["agents"] = {
            "netflix_ai_agent": {
                "name": "Netflix AI Agent",
                "type": "local",
                "status": "active",
                "config": {
                    "model": "gemini-1.5-flash",
                    "specialization": "streaming_entertainment"
                }
            }
        }
        
        # Update tenant policy settings
        netflix_tenant.policy_settings = existing_settings
        db.commit()
        
        print("✅ Merged Netflix AI Agent into existing policy settings")
        print(f"Updated policy settings: {json.dumps(existing_settings, indent=2)}")

if __name__ == "__main__":
    merge_netflix_agent()
