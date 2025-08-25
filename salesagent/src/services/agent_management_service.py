"""
Agent Management Service - High-level operations for agent discovery and management
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, UTC
import logging

from src.repositories.agents_repo import agent_repository
from src.core.schemas.agent import AgentConfig, AgentStatus, AgentType, AgentReport


logger = logging.getLogger(__name__)


class AgentManagementService:
    """Service for managing agents across tenants"""
    
    def __init__(self):
        self.repository = agent_repository
    
    def discover_active_agents(
        self,
        include_tenant_ids: Optional[List[str]] = None,
        exclude_tenant_ids: Optional[List[str]] = None,
        include_agent_ids: Optional[List[str]] = None,
        agent_types: Optional[List[str]] = None
    ) -> List[Tuple[AgentConfig, str, str]]:
        """
        Discover all active agents across tenants
        
        Returns:
            List of tuples: (AgentConfig, tenant_id, tenant_name)
        """
        try:
            logger.info(f"Discovering active agents - include_tenants: {include_tenant_ids}, "
                       f"exclude_tenants: {exclude_tenant_ids}, agent_types: {agent_types}")
            
            agents = self.repository.list_active_agents_across_tenants(
                include_tenant_ids=include_tenant_ids,
                exclude_tenant_ids=exclude_tenant_ids,
                include_agent_ids=include_agent_ids,
                agent_types=agent_types,
                status=AgentStatus.ACTIVE
            )
            
            logger.info(f"Discovered {len(agents)} active agents")
            return agents
            
        except Exception as e:
            logger.error(f"Error discovering active agents: {e}")
            return []
    
    def get_agent_details(self, agent_id: str, tenant_id: str) -> Optional[AgentConfig]:
        """Get detailed information about a specific agent"""
        try:
            return self.repository.get_agent_by_id(agent_id, tenant_id)
        except Exception as e:
            logger.error(f"Error getting agent details for {agent_id} in tenant {tenant_id}: {e}")
            return None
    
    def update_agent_status(self, agent_id: str, tenant_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        try:
            logger.info(f"Updating agent {agent_id} in tenant {tenant_id} to status {status}")
            success = self.repository.update_agent_status(agent_id, tenant_id, status)
            
            if success:
                logger.info(f"Successfully updated agent {agent_id} status to {status}")
            else:
                logger.warning(f"Failed to update agent {agent_id} status to {status}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            return False
    
    def create_default_agents_for_tenant(self, tenant_id: str) -> List[AgentConfig]:
        """Create default agents for a new tenant"""
        try:
            logger.info(f"Creating default agents for tenant {tenant_id}")
            agents = self.repository.create_default_agents_for_tenant(tenant_id)
            
            logger.info(f"Created {len(agents)} default agents for tenant {tenant_id}")
            return agents
            
        except Exception as e:
            logger.error(f"Error creating default agents for tenant {tenant_id}: {e}")
            return []
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about agents across all tenants"""
        try:
            all_agents = self.repository.list_active_agents_across_tenants()
            
            stats = {
                'total_agents': len(all_agents),
                'active_agents': len([a for a, _, _ in all_agents if a.status == AgentStatus.ACTIVE]),
                'inactive_agents': len([a for a, _, _ in all_agents if a.status == AgentStatus.INACTIVE]),
                'error_agents': len([a for a, _, _ in all_agents if a.status == AgentStatus.ERROR]),
                'agent_types': {},
                'tenants_with_agents': len(set(tenant_id for _, tenant_id, _ in all_agents))
            }
            
            # Count by agent type
            for agent, _, _ in all_agents:
                agent_type = agent.type
                stats['agent_types'][agent_type] = stats['agent_types'].get(agent_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting agent statistics: {e}")
            return {
                'total_agents': 0,
                'active_agents': 0,
                'inactive_agents': 0,
                'error_agents': 0,
                'agent_types': {},
                'tenants_with_agents': 0
            }
    
    def validate_agent_config(self, agent_config: AgentConfig) -> Tuple[bool, List[str]]:
        """Validate agent configuration"""
        errors = []
        
        # Check required fields
        if not agent_config.agent_id:
            errors.append("Agent ID is required")
        
        if not agent_config.tenant_id:
            errors.append("Tenant ID is required")
        
        if not agent_config.name:
            errors.append("Agent name is required")
        
        if not agent_config.type:
            errors.append("Agent type is required")
        
        # Validate agent type
        if agent_config.type not in [t.value for t in AgentType]:
            errors.append(f"Invalid agent type: {agent_config.type}")
        
        # Validate endpoint URL for external agents
        if agent_config.type in ['mcp', 'external'] and not agent_config.endpoint_url:
            errors.append(f"Endpoint URL is required for {agent_config.type} agents")
        
        return len(errors) == 0, errors
    
    def get_agents_by_tenant(self, tenant_id: str) -> List[AgentConfig]:
        """Get all agents for a specific tenant"""
        try:
            agents = self.repository.list_active_agents_across_tenants(
                include_tenant_ids=[tenant_id]
            )
            return [agent for agent, _, _ in agents]
        except Exception as e:
            logger.error(f"Error getting agents for tenant {tenant_id}: {e}")
            return []
    
    def add_agent_to_tenant(self, tenant_id: str, agent_id: str, agent_config: Dict[str, Any]) -> bool:
        """Add a new agent to a tenant"""
        try:
            return self.repository.add_agent_to_tenant(tenant_id, agent_id, agent_config)
        except Exception as e:
            logger.error(f"Error adding agent {agent_id} to tenant {tenant_id}: {e}")
            return False
    
    def update_agent_config(self, agent_id: str, tenant_id: str, config_updates: Dict[str, Any]) -> bool:
        """Update agent configuration"""
        try:
            return self.repository.update_agent_config(agent_id, tenant_id, config_updates)
        except Exception as e:
            logger.error(f"Error updating agent {agent_id} config: {e}")
            return False
    
    def delete_agent(self, agent_id: str, tenant_id: str) -> bool:
        """Delete an agent"""
        try:
            return self.repository.delete_agent(agent_id, tenant_id)
        except Exception as e:
            logger.error(f"Error deleting agent {agent_id}: {e}")
            return False


# Global instance for easy access
agent_management_service = AgentManagementService()
