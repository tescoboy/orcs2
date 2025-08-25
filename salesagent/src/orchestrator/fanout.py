"""
Fanout Orchestrator - Calls all agent provider endpoints concurrently
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, UTC

import httpx

from src.core.schemas.agent import AgentConfig, AgentSelectRequest, AgentReport, AgentStatus
from src.services.agent_management_service import agent_management_service
from src.orchestrator.mcp_client import mcp_client

logger = logging.getLogger(__name__)


class FanoutOrchestrator:
    """Orchestrator that fans out requests to all agent provider endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 10, max_concurrency: int = 12):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
    
    async def fanout_to_agents(
        self,
        request: AgentSelectRequest,
        include_tenant_ids: Optional[List[str]] = None,
        exclude_tenant_ids: Optional[List[str]] = None,
        include_agent_ids: Optional[List[str]] = None,
        agent_types: Optional[List[str]] = None
    ) -> Tuple[List[Dict[str, Any]], List[AgentReport]]:
        """
        Fan out request to all active agents and collect results
        
        Returns:
            Tuple of (products_list, agent_reports)
        """
        start_time = time.time()
        
        try:
            # Discover all active agents
            agents_data = agent_management_service.discover_active_agents(
                include_tenant_ids=include_tenant_ids,
                exclude_tenant_ids=exclude_tenant_ids,
                include_agent_ids=include_agent_ids,
                agent_types=agent_types
            )
            
            logger.info(f"Fanning out to {len(agents_data)} agents")
            
            if not agents_data:
                logger.warning("No active agents found for fanout")
                return [], []
            
            # Create tasks for all agents
            tasks = []
            for agent, tenant_id, tenant_name in agents_data:
                task = self._call_agent_provider(agent, tenant_id, request)
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            all_products = []
            agent_reports = []
            
            for i, result in enumerate(results):
                agent, tenant_id, tenant_name = agents_data[i]
                
                if isinstance(result, Exception):
                    # Agent call failed
                    report = AgentReport(
                        agent_id=agent.agent_id,
                        tenant_id=tenant_id,
                        status=AgentStatus.ERROR,
                        error_message=str(result),
                        products_count=0,
                        executed_at=datetime.now(UTC)
                    )
                    agent_reports.append(report)
                    logger.error(f"Agent {agent.agent_id} failed: {result}")
                    
                else:
                    # Agent call succeeded
                    products, execution_time_ms = result
                    
                    # Add products to collection
                    for product in products:
                        product["source_agent_id"] = agent.agent_id
                        product["publisher_tenant_id"] = tenant_id
                        all_products.append(product)
                    
                    # Create report
                    report = AgentReport(
                        agent_id=agent.agent_id,
                        tenant_id=tenant_id,
                        status=AgentStatus.ACTIVE,
                        latency_ms=execution_time_ms,
                        products_count=len(products),
                        executed_at=datetime.now(UTC)
                    )
                    agent_reports.append(report)
                    
                    logger.info(f"Agent {agent.agent_id} returned {len(products)} products in {execution_time_ms}ms")
            
            total_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Fanout completed in {total_time_ms}ms - {len(all_products)} total products from {len(agent_reports)} agents")
            
            return all_products, agent_reports
            
        except Exception as e:
            logger.error(f"Error in fanout orchestration: {e}", exc_info=True)
            return [], []
    
    async def _call_agent_provider(
        self, 
        agent: AgentConfig, 
        tenant_id: str, 
        request: AgentSelectRequest
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Call a single agent provider endpoint
        """
        async with self.semaphore:
            start_time = time.time()
            
            try:
                # Handle different agent types
                if agent.type == "mcp":
                    # MCP agent - use MCP client
                    return await self._call_mcp_agent(agent, request)
                elif agent.endpoint_url and agent.endpoint_url.startswith('http'):
                    # External agent with custom endpoint
                    return await self._call_external_agent(agent, request)
                else:
                    # Local agent
                    return await self._call_local_agent(agent, tenant_id, request)
                        
            except asyncio.TimeoutError:
                execution_time_ms = int((time.time() - start_time) * 1000)
                logger.warning(f"Agent {agent.agent_id} timed out after {execution_time_ms}ms")
                raise Exception(f"Timeout after {execution_time_ms}ms")
                
            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)
                logger.error(f"Agent {agent.agent_id} failed after {execution_time_ms}ms: {e}")
                raise
    
    async def _call_mcp_agent(
        self, 
        agent: AgentConfig, 
        request: AgentSelectRequest
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Call an MCP-compliant agent
        """
        try:
            result = await mcp_client.call_mcp_agent(
                endpoint_url=agent.endpoint_url,
                request=request,
                agent_config=agent.config
            )
            
            products = result.get("products", [])
            execution_time_ms = result.get("execution_time_ms", 0)
            
            # Add source information to products
            for product in products:
                product["source_agent_id"] = agent.agent_id
                product["publisher_tenant_id"] = agent.tenant_id
            
            return products, execution_time_ms
            
        except Exception as e:
            logger.error(f"MCP agent {agent.agent_id} failed: {e}")
            raise
    
    async def _call_external_agent(
        self, 
        agent: AgentConfig, 
        request: AgentSelectRequest
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Call an external agent with custom endpoint
        """
        try:
            url = f"{agent.endpoint_url}/select_products"
            
            # Prepare request payload
            payload = {
                "prompt": request.prompt,
                "max_results": request.max_results,
                "filters": request.filters,
                "locale": request.locale,
                "currency": request.currency,
                "timeout_seconds": request.timeout_seconds
            }
            
            # Make HTTP request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get("products", [])
                    execution_time_ms = data.get("execution_time_ms", 0)
                    
                    # Add source information to products
                    for product in products:
                        product["source_agent_id"] = agent.agent_id
                        product["publisher_tenant_id"] = agent.tenant_id
                    
                    return products, execution_time_ms
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    raise Exception(error_msg)
                    
        except Exception as e:
            logger.error(f"External agent {agent.agent_id} failed: {e}")
            raise
    
    async def _call_local_agent(
        self, 
        agent: AgentConfig, 
        tenant_id: str, 
        request: AgentSelectRequest
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Call a local agent
        """
        try:
            agent_type = agent.type
            url = f"{self.base_url}/tenant/{tenant_id}/agent/{agent_type}/select_products"
            
            # Prepare request payload
            payload = {
                "prompt": request.prompt,
                "max_results": request.max_results,
                "filters": request.filters,
                "locale": request.locale,
                "currency": request.currency,
                "timeout_seconds": request.timeout_seconds
            }
            
            # Make HTTP request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get("products", [])
                    execution_time_ms = data.get("execution_time_ms", 0)
                    
                    # Add source information to products
                    for product in products:
                        product["source_agent_id"] = agent.agent_id
                        product["publisher_tenant_id"] = tenant_id
                    
                    return products, execution_time_ms
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    raise Exception(error_msg)
                    
        except Exception as e:
            logger.error(f"Local agent {agent.agent_id} failed: {e}")
            raise
    
    async def call_local_agent_in_process(
        self,
        agent: AgentConfig,
        tenant_id: str,
        request: AgentSelectRequest
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Call a local agent in-process (avoiding HTTP overhead)
        """
        start_time = time.time()
        
        try:
            # Import the local agent provider function
            from src.admin.blueprints.agent_providers import select_products
            
            # Create a mock request object for the Flask function
            class MockRequest:
                def __init__(self, json_data):
                    self.json_data = json_data
                
                def get_json(self):
                    return self.json_data
            
            # Call the local function directly
            mock_request = MockRequest({
                "prompt": request.prompt,
                "max_results": request.max_results,
                "filters": request.filters,
                "locale": request.locale,
                "currency": request.currency,
                "timeout_seconds": request.timeout_seconds
            })
            
            # Note: This would need to be adapted to work with Flask's request context
            # For now, we'll use the HTTP approach for consistency
            return await self._call_agent_provider(agent, tenant_id, request)
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"In-process call to agent {agent.agent_id} failed: {e}")
            raise


# Global instance
fanout_orchestrator = FanoutOrchestrator()
