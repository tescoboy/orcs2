#!/usr/bin/env python3

import sys
from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant
import json

def add_agent_to_tenant(tenant_id):
    """Add an agent to a specific tenant"""
    with get_db_session() as db:
        # Find the tenant
        tenant = db.query(Tenant).filter_by(tenant_id=tenant_id).first()
        
        if not tenant:
            print(f"❌ Tenant '{tenant_id}' not found!")
            print("\nAvailable tenants:")
            all_tenants = db.query(Tenant).all()
            for t in all_tenants:
                print(f"  - {t.tenant_id}: {t.name}")
            return False
        
        print(f"✅ Found tenant: {tenant.tenant_id} - {tenant.name}")
        
        # Get existing policy settings or create new ones
        existing_settings = tenant.policy_settings or {}
        
        # Create agent ID based on tenant
        agent_id = f"{tenant_id}_ai_agent"
        
        # Add agent configuration
        existing_settings["agents"] = {
            agent_id: {
                "name": f"{tenant.name} AI Agent",
                "type": "local",
                "status": "active",
                "config": {
                    "model": "gemini-1.5-flash",
                    "specialization": "general"
                }
            }
        }
        
        # Update tenant policy settings
        tenant.policy_settings = existing_settings
        db.commit()
        
        print(f"✅ Added AI Agent to tenant '{tenant_id}'")
        print(f"Agent ID: {agent_id}")
        print(f"Agent config: {json.dumps(existing_settings, indent=2)}")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_agent_to_tenant.py <tenant_id>")
        print("\nExample: python add_agent_to_tenant.py harvinads_hg")
        sys.exit(1)
    
    tenant_id = sys.argv[1]
    success = add_agent_to_tenant(tenant_id)
    if success:
        print("\n🎉 Agent added successfully! The tenant should now appear in orchestrator searches.")
    else:
        sys.exit(1)
