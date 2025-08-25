#!/usr/bin/env python3

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant
from src.repositories.agents_repo import AgentRepository

# Check all tenants
with get_db_session() as db:
    all_tenants = db.query(Tenant).all()
    print(f'Found {len(all_tenants)} total tenants:')
    for t in all_tenants:
        print(f'  - {t.tenant_id}: {t.name}, active: {t.is_active}, policy_settings: {bool(t.policy_settings)}')

print("\n" + "="*50)

# Check agent discovery
repo = AgentRepository()
agents = repo.list_active_agents_across_tenants()
print(f'Agent discovery found {len(agents)} agents:')
for agent, tenant_id, tenant_name in agents:
    print(f'  - {agent.agent_id} ({agent.type}) in {tenant_id} ({tenant_name})')

print("\n" + "="*50)

# Check Netflix tenant specifically
with get_db_session() as db:
    netflix_tenant = db.query(Tenant).filter_by(tenant_id='netflix').first()
    if netflix_tenant:
        print(f'Netflix tenant details:')
        print(f'  - ID: {netflix_tenant.tenant_id}')
        print(f'  - Name: {netflix_tenant.name}')
        print(f'  - Active: {netflix_tenant.is_active}')
        print(f'  - Policy settings: {netflix_tenant.policy_settings}')
        
        # Test agent extraction for Netflix tenant
        repo = AgentRepository()
        netflix_agents = repo._get_tenant_agents(netflix_tenant)
        print(f'  - Netflix agents found: {len(netflix_agents)}')
        for agent in netflix_agents:
            print(f'    * {agent.agent_id}: {agent.name} ({agent.type})')
    else:
        print('Netflix tenant not found!')
