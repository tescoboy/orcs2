#!/usr/bin/env python3
"""
Simple test script to verify agent discovery works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.repositories.agents_repo import AgentRepository
from src.core.database.database_session import get_db_session

def test_agent_discovery():
    """Test agent discovery directly"""
    print("🔍 Testing agent discovery...")
    
    try:
        with get_db_session() as db_session:
            repo = AgentRepository(db_session)
            agents = repo.list_active_agents_across_tenants()
            
            print(f"✅ Found {len(agents)} agents:")
            for agent, tenant_id, tenant_name in agents:
                print(f"  - {agent.name} ({agent.type}) in {tenant_name}")
                
            return len(agents) > 0
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_agent_discovery()
    if success:
        print("🎉 Agent discovery test PASSED!")
        sys.exit(0)
    else:
        print("💥 Agent discovery test FAILED!")
        sys.exit(1)
