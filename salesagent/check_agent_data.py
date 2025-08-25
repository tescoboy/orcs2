#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant
import json

with get_db_session() as db:
    tenant = db.query(Tenant).filter_by(tenant_id='tech_publisher').first()
    if tenant and tenant.policy_settings:
        print("Policy settings found:")
        print(f"Type: {type(tenant.policy_settings)}")
        print(f"Content: {tenant.policy_settings}")
        
        # Handle both dict and JSON string cases
        config = {}
        if isinstance(tenant.policy_settings, dict):
            config = tenant.policy_settings
        else:
            try:
                config = json.loads(tenant.policy_settings)
            except (json.JSONDecodeError, TypeError):
                print("Error parsing policy_settings")
                exit(1)
        
        agents = config.get('agents', {})
        print("\nAgents in config:")
        for agent_id, agent_data in agents.items():
            print(f"  {agent_id}: {agent_data}")
    else:
        print("No policy settings found")
