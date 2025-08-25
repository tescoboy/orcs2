"""
Orchestrator Service - Main service for coordinating multi-agent product discovery
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC

from src.core.schemas.agent import AgentSelectRequest, AgentReport
from src.orchestrator.fanout import fanout_orchestrator
from src.orchestrator.normalize import product_normalizer
from src.services.agent_management_service import agent_management_service
from src.orchestrator.performance import performance_monitor, concurrency_optimizer, cache_manager

logger = logging.getLogger(__name__)


class OrchestratorService:
    """Main orchestrator service for multi-agent product discovery"""
    
    def __init__(self):
        self.fanout = fanout_orchestrator
        self.normalizer = product_normalizer
    
    async def orchestrate(
        self,
        request: AgentSelectRequest,
        include_tenant_ids: Optional[List[str]] = None,
        exclude_tenant_ids: Optional[List[str]] = None,
        include_agent_ids: Optional[List[str]] = None,
        agent_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main orchestration method - fan out to all agents, aggregate, normalize, dedupe, sort
        
        Returns:
            Dict with products, agent_reports, and metadata
        """
        # Start performance monitoring
        metrics = performance_monitor.start_operation()
        
        try:
            logger.info(f"Starting orchestration with prompt: '{request.prompt[:100]}...'")
            
            # Check cache for similar requests
            cache_key = self._generate_cache_key(request, include_tenant_ids, exclude_tenant_ids, 
                                               include_agent_ids, agent_types)
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info("Returning cached result")
                metrics.total_products_found = len(cached_result.get("products", []))
                metrics.total_products_after_sort = len(cached_result.get("products", []))
                performance_monitor.end_operation(metrics)
                return cached_result
            
            # Step 1: Fan out to all agents
            all_products, agent_reports = await self.fanout.fanout_to_agents(
                request=request,
                include_tenant_ids=include_tenant_ids,
                exclude_tenant_ids=exclude_tenant_ids,
                include_agent_ids=include_agent_ids,
                agent_types=agent_types
            )
            
            # Step 2: Process products (normalize, dedupe, sort, truncate)
            processed_products = self.normalizer.process_products(
                products=all_products,
                max_results=request.max_results
            )
            
            # Step 3: Calculate statistics
            total_time_ms = int((time.time() - metrics.start_time) * 1000)
            
            # Count successful vs failed agents
            successful_agents = [r for r in agent_reports if r.status == "active"]
            failed_agents = [r for r in agent_reports if r.status != "active"]
            
            # Calculate total products found by successful agents
            total_products_found = sum(r.products_count for r in successful_agents)
            
            # Update performance metrics
            metrics.total_agents_contacted = len(agent_reports)
            metrics.successful_agents = len(successful_agents)
            metrics.failed_agents = len(failed_agents)
            metrics.total_products_found = total_products_found
            metrics.total_products_after_dedupe = len(processed_products)
            metrics.total_products_after_sort = len(processed_products)
            
            # Extract agent response times from reports
            for report in agent_reports:
                if hasattr(report, 'response_time_ms') and report.response_time_ms:
                    metrics.agent_response_times[report.agent_id] = report.response_time_ms
                if hasattr(report, 'products_count'):
                    metrics.agent_product_counts[report.agent_id] = report.products_count
            
            # Build response
            response = {
                "products": processed_products,
                "agent_reports": [report.dict() for report in agent_reports],
                "metadata": {
                    "total_agents_contacted": len(agent_reports),
                    "successful_agents": len(successful_agents),
                    "failed_agents": len(failed_agents),
                    "total_products_found": total_products_found,
                    "total_products_after_dedupe": len(processed_products),
                    "orchestration_time_ms": total_time_ms,
                    "request_id": f"orch_{int(metrics.start_time)}",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "performance": {
                        "avg_response_time_ms": metrics.avg_response_time_ms,
                        "median_response_time_ms": metrics.median_response_time_ms,
                        "success_rate": metrics.success_rate
                    }
                }
            }
            
            # Cache the result
            cache_manager.set(cache_key, response)
            
            logger.info(f"Orchestration completed in {total_time_ms}ms: "
                       f"{len(successful_agents)}/{len(agent_reports)} agents successful, "
                       f"{total_products_found} products found, "
                       f"{len(processed_products)} products returned")
            
            # End performance monitoring
            performance_monitor.end_operation(metrics)
            
            return response
            
        except Exception as e:
            total_time_ms = int((time.time() - metrics.start_time) * 1000)
            logger.error(f"Orchestration failed after {total_time_ms}ms: {e}", exc_info=True)
            
            # Update metrics for error case
            metrics.errors.append(str(e))
            performance_monitor.end_operation(metrics)
            
            return {
                "products": [],
                "agent_reports": [],
                "metadata": {
                    "total_agents_contacted": 0,
                    "successful_agents": 0,
                    "failed_agents": 0,
                    "total_products_found": 0,
                    "total_products_after_dedupe": 0,
                    "orchestration_time_ms": int((time.time() - metrics.start_time) * 1000),
                    "request_id": f"orch_{int(metrics.start_time)}",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "error": str(e)
                }
            }
    
    def _generate_cache_key(
        self,
        request: AgentSelectRequest,
        include_tenant_ids: Optional[List[str]] = None,
        exclude_tenant_ids: Optional[List[str]] = None,
        include_agent_ids: Optional[List[str]] = None,
        agent_types: Optional[List[str]] = None
    ) -> str:
        """Generate a cache key for the request"""
        import hashlib
        import json
        
        # Create a unique key based on request parameters
        key_data = {
            "prompt": request.prompt,
            "max_results": request.max_results,
            "filters": request.filters,
            "locale": request.locale,
            "currency": request.currency,
            "include_tenant_ids": sorted(include_tenant_ids or []),
            "exclude_tenant_ids": sorted(exclude_tenant_ids or []),
            "include_agent_ids": sorted(include_agent_ids or []),
            "agent_types": sorted(agent_types or [])
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return f"orch_cache_{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def get_orchestration_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the orchestrator including performance metrics
        """
        try:
            # Get agent statistics
            agent_stats = agent_management_service.get_agent_statistics()
            
            # Get performance metrics
            performance_summary = performance_monitor.get_performance_summary()
            concurrency_stats = concurrency_optimizer.get_stats()
            cache_stats = cache_manager.get_stats()
            
            return {
                "orchestrator_status": "active",
                "agent_statistics": agent_stats,
                "performance_metrics": performance_summary,
                "concurrency_stats": concurrency_stats,
                "cache_stats": cache_stats,
                "last_updated": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting orchestration statistics: {e}")
            return {
                "orchestrator_status": "error",
                "error": str(e),
                "last_updated": datetime.now(UTC).isoformat()
            }


# Global instance
orchestrator_service = OrchestratorService()
