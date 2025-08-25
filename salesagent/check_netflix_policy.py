#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant

with get_db_session() as db:
    netflix = db.query(Tenant).filter_by(tenant_id='netflix').first()
    if netflix:
        print(f'Netflix tenant: {netflix.tenant_id}')
        print(f'Policy settings: {netflix.policy_settings}')
        
        if netflix.policy_settings and 'agents' in netflix.policy_settings:
            agents = netflix.policy_settings['agents']
            print(f'Agents found: {len(agents)}')
            for agent_id, agent_data in agents.items():
                print(f'  - {agent_id}: {agent_data}')
        else:
            print('No agents found in policy settings')
    else:
        print('Netflix tenant not found')
