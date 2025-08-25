#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant
import json

def add_harvinads_agent():
    """Add an agent to the harvinads tenant"""
    with get_db_session() as db:
        # Find the harvinads tenant
        harvinads_tenant = db.query(Tenant).filter(Tenant.tenant_id.like('%harvinads%')).first()
        
        if not harvinads_tenant:
            print("Harvinads tenant not found!")
            return
        
        print(f"Found tenant: {harvinads_tenant.tenant_id} - {harvinads_tenant.name}")
        
        # Get existing policy settings or create new ones
        existing_settings = harvinads_tenant.policy_settings or {}
        
        # Add agent configuration
        existing_settings["agents"] = {
            "harvinads_ai_agent": {
                "name": "Harvinads AI Agent",
                "type": "local",
                "status": "active",
                "config": {
                    "model": "gemini-1.5-flash",
                    "specialization": "true_crime_entertainment"
                }
            }
        }
        
        # Update tenant policy settings
        harvinads_tenant.policy_settings = existing_settings
        db.commit()
        
        print("✅ Added Harvinads AI Agent to harvinads tenant")
        print(f"Agent config: {json.dumps(existing_settings, indent=2)}")

if __name__ == "__main__":
    add_harvinads_agent()
