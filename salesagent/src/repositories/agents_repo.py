"""
Agent Repository - Cross-tenant agent discovery and management
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant, Principal
from src.core.schemas.agent import AgentConfig, AgentStatus


class AgentRepository:
    """Repository for managing agents across all tenants"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
    
    def list_active_agents_across_tenants(
        self,
        include_tenant_ids: Optional[List[str]] = None,
        exclude_tenant_ids: Optional[List[str]] = None,
        include_agent_ids: Optional[List[str]] = None,
        agent_types: Optional[List[str]] = None,
        status: Optional[AgentStatus] = AgentStatus.ACTIVE
    ) -> List[Tuple[AgentConfig, str, str]]:
        """
        Get all active agents across tenants with optional filtering
        
        Returns:
            List of tuples: (AgentConfig, tenant_id, tenant_name)
        """
        try:
            # Use the session passed to constructor, or create a new one
            if self.db_session:
                db_session = self.db_session
            else:
                with get_db_session() as db_session:
                    return self._list_agents_with_session(
                        db_session, include_tenant_ids, exclude_tenant_ids, 
                        include_agent_ids, agent_types, status
                    )
            
            return self._list_agents_with_session(
                db_session, include_tenant_ids, exclude_tenant_ids, 
                include_agent_ids, agent_types, status
            )
            
        except Exception as e:
            print(f"Error listing agents across tenants: {e}")
            return []
    
    def _list_agents_with_session(
        self,
        db_session,
        include_tenant_ids: Optional[List[str]] = None,
        exclude_tenant_ids: Optional[List[str]] = None,
        include_agent_ids: Optional[List[str]] = None,
        agent_types: Optional[List[str]] = None,
        status: Optional[AgentStatus] = AgentStatus.ACTIVE
    ) -> List[Tuple[AgentConfig, str, str]]:
        """Helper method to list agents with a specific database session"""
        # Query all tenants that match our filters
        tenant_query = db_session.query(Tenant)
        
        if include_tenant_ids:
            tenant_query = tenant_query.filter(Tenant.tenant_id.in_(include_tenant_ids))
        
        if exclude_tenant_ids:
            tenant_query = tenant_query.filter(~Tenant.tenant_id.in_(exclude_tenant_ids))
        
        tenants = tenant_query.all()
        
        agents = []
        
        for tenant in tenants:
            # Get agents for this tenant
            tenant_agents = self._get_tenant_agents(tenant, include_agent_ids, agent_types, status)
            
            for agent in tenant_agents:
                agents.append((agent, tenant.tenant_id, tenant.name))
        
        return agents
    
    def _get_tenant_agents(
        self,
        tenant: Tenant,
        include_agent_ids: Optional[List[str]] = None,
        agent_types: Optional[List[str]] = None,
        status: Optional[AgentStatus] = AgentStatus.ACTIVE
    ) -> List[AgentConfig]:
        """
        Get agents for a specific tenant
        """
        try:
            # Parse tenant config to extract agent configurations from policy_settings
            import json
            config = {}
            if tenant.policy_settings:
                # Handle both dict and JSON string cases
                if isinstance(tenant.policy_settings, dict):
                    config = tenant.policy_settings
                else:
                    try:
                        config = json.loads(tenant.policy_settings)
                    except (json.JSONDecodeError, TypeError):
                        config = {}
            agents_config = config.get('agents', {})
            
            agents = []
            
            for agent_id, agent_data in agents_config.items():
                # Apply filters
                if include_agent_ids and agent_id not in include_agent_ids:
                    continue
                
                if agent_types and agent_data.get('type') not in agent_types:
                    continue
                
                if status and agent_data.get('status') != status:
                    continue
                
                # Create AgentConfig object
                agent_config = AgentConfig(
                    agent_id=agent_id,
                    tenant_id=tenant.tenant_id,
                    name=agent_data.get('name', f"{tenant.name} {agent_id}"),
                    type=agent_data.get('type', 'local_ai'),
                    status=AgentStatus(agent_data.get('status', 'active')),
                    endpoint_url=agent_data.get('endpoint_url'),
                    config=agent_data.get('config', {}),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                
                agents.append(agent_config)
            
            return agents
            
        except Exception as e:
            print(f"Error getting agents for tenant {tenant.tenant_id}: {e}")
            return []
    
    def get_agent_by_id(self, agent_id: str, tenant_id: str) -> Optional[AgentConfig]:
        """Get a specific agent by ID and tenant"""
        try:
            tenant = self.db_session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if not tenant:
                return None
            
            agents = self._get_tenant_agents(tenant, include_agent_ids=[agent_id])
            return agents[0] if agents else None
            
        except Exception as e:
            print(f"Error getting agent {agent_id} for tenant {tenant_id}: {e}")
            return None
    
    def update_agent_status(self, agent_id: str, tenant_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        try:
            tenant = self.db_session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if not tenant:
                return False
            
            existing_settings = tenant.policy_settings or {}
            agents_config = existing_settings.get('agents', {})
            
            if agent_id not in agents_config:
                return False
            
            agents_config[agent_id]['status'] = status.value
            existing_settings['agents'] = agents_config
            
            tenant.policy_settings = existing_settings
            self.db_session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error updating agent status: {e}")
            self.db_session.rollback()
            return False
    
    def create_default_agents_for_tenant(self, tenant_id: str) -> List[AgentConfig]:
        """Create default agents for a new tenant"""
        try:
            tenant = self.db_session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if not tenant:
                return []
            
            # Get existing policy settings or create new ones
            existing_settings = tenant.policy_settings or {}
            agents_config = existing_settings.get('agents', {})
            
            # Create default local AI agent
            default_agent_id = f"{tenant_id}_local_ai"
            agents_config[default_agent_id] = {
                'name': f"{tenant.name} Local AI Agent",
                'type': 'local',
                'status': 'active',
                'config': {
                    'model': 'gemini-1.5-flash',
                    'specialization': 'general'
                }
            }
            
            existing_settings['agents'] = agents_config
            tenant.policy_settings = existing_settings
            self.db_session.commit()
            
            # Return the created agent
            return self._get_tenant_agents(tenant, include_agent_ids=[default_agent_id])
            
        except Exception as e:
            print(f"Error creating default agents for tenant {tenant_id}: {e}")
            self.db_session.rollback()
            return []
    
    def add_agent_to_tenant(self, tenant_id: str, agent_id: str, agent_config: Dict[str, Any]) -> bool:
        """Add a new agent to a tenant"""
        try:
            tenant = self.db_session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if not tenant:
                return False
            
            existing_settings = tenant.policy_settings or {}
            agents_config = existing_settings.get('agents', {})
            
            # Add the new agent
            agents_config[agent_id] = agent_config
            
            existing_settings['agents'] = agents_config
            tenant.policy_settings = existing_settings
            self.db_session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error adding agent {agent_id} to tenant {tenant_id}: {e}")
            self.db_session.rollback()
            return False
    
    def update_agent_config(self, agent_id: str, tenant_id: str, config_updates: Dict[str, Any]) -> bool:
        """Update agent configuration"""
        try:
            tenant = self.db_session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if not tenant:
                return False
            
            config = tenant.config or {}
            agents_config = config.get('agents', {})
            
            if agent_id not in agents_config:
                return False
            
            # Update the agent configuration
            current_config = agents_config[agent_id]
            current_config.update(config_updates)
            agents_config[agent_id] = current_config
            
            config['agents'] = agents_config
            tenant.config = config
            self.db_session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error updating agent {agent_id} config: {e}")
            self.db_session.rollback()
            return False
    
    def delete_agent(self, agent_id: str, tenant_id: str) -> bool:
        """Delete an agent"""
        try:
            tenant = self.db_session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if not tenant:
                return False
            
            config = tenant.config or {}
            agents_config = config.get('agents', {})
            
            if agent_id not in agents_config:
                return False
            
            # Remove the agent
            del agents_config[agent_id]
            
            config['agents'] = agents_config
            tenant.config = config
            self.db_session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error deleting agent {agent_id}: {e}")
            self.db_session.rollback()
            return False


# Global instance for easy access
agent_repository = AgentRepository()
