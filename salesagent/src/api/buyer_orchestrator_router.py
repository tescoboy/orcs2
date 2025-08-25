"""
Buyer Orchestrator API Router - Public endpoint for cross-tenant product discovery
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional

from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from src.core.schemas.agent import AgentSelectRequest
from src.services.orchestrator_service import orchestrator_service

logger = logging.getLogger(__name__)

# Create Blueprint
buyer_orchestrator_bp = Blueprint("buyer_orchestrator", __name__, url_prefix="/buyer")


@buyer_orchestrator_bp.route("/orchestrate", methods=["POST"])
def orchestrate_products():
    """
    Public endpoint for cross-tenant product orchestration
    
    This endpoint is independent of tenant cookies and discovers products
    across all tenants using the multi-agent orchestrator.
    """
    try:
        # Get request data
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                "error": "Request body is required",
                "status": "error"
            }), 400
        
        # Validate request
        try:
            agent_request = AgentSelectRequest(**request_data)
        except ValidationError as e:
            return jsonify({
                "error": f"Invalid request format: {str(e)}",
                "status": "error"
            }), 400
        
        # Get filter parameters from query string
        include_tenant_ids = request.args.getlist('include_tenant_ids')
        exclude_tenant_ids = request.args.getlist('exclude_tenant_ids')
        include_agent_ids = request.args.getlist('include_agent_ids')
        agent_types = request.args.getlist('agent_types')
        
        # Convert empty lists to None
        include_tenant_ids = include_tenant_ids if include_tenant_ids else None
        exclude_tenant_ids = exclude_tenant_ids if exclude_tenant_ids else None
        include_agent_ids = include_agent_ids if include_agent_ids else None
        agent_types = agent_types if agent_types else None
        
        logger.info(f"Orchestration request: prompt='{agent_request.prompt[:100]}...', "
                   f"max_results={agent_request.max_results}, "
                   f"include_tenants={include_tenant_ids}, "
                   f"exclude_tenants={exclude_tenant_ids}, "
                   f"agent_types={agent_types}")
        
        # Call orchestrator service
        response = asyncio.run(orchestrator_service.orchestrate(
            request=agent_request,
            include_tenant_ids=include_tenant_ids,
            exclude_tenant_ids=exclude_tenant_ids,
            include_agent_ids=include_agent_ids,
            agent_types=agent_types
        ))
        
        # Return response
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in orchestration endpoint: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@buyer_orchestrator_bp.route("/orchestrate/health", methods=["GET"])
def orchestration_health():
    """
    Health check endpoint for the orchestrator
    """
    try:
        stats = orchestrator_service.get_orchestration_statistics()
        return jsonify({
            "status": "healthy",
            "orchestrator": stats,
            "timestamp": stats.get("last_updated")
        })
        
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@buyer_orchestrator_bp.route("/orchestrate/agents", methods=["GET"])
def list_available_agents():
    """
    List all available agents for orchestration
    """
    try:
        from src.services.agent_management_service import agent_management_service
        
        # Get all active agents
        agents_data = agent_management_service.discover_active_agents()
        
        # Format response
        agents = []
        for agent, tenant_id, tenant_name in agents_data:
            agents.append({
                "agent_id": agent.agent_id,
                "tenant_id": tenant_id,
                "tenant_name": tenant_name,
                "name": agent.name,
                "type": agent.type,
                "status": agent.status,
                "endpoint_url": agent.endpoint_url
            })
        
        return jsonify({
            "agents": agents,
            "total_agents": len(agents),
            "agent_types": list(set(agent["type"] for agent in agents))
        })
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@buyer_orchestrator_bp.route("/orchestrate/tenants", methods=["GET"])
def list_available_tenants():
    """
    List all tenants with active agents
    """
    try:
        from src.services.agent_management_service import agent_management_service
        
        # Get all active agents to extract unique tenants
        agents_data = agent_management_service.discover_active_agents()
        
        # Group by tenant
        tenants = {}
        for agent, tenant_id, tenant_name in agents_data:
            if tenant_id not in tenants:
                tenants[tenant_id] = {
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "agent_count": 0,
                    "active_agents": 0,
                    "agent_types": set()
                }
            
            tenants[tenant_id]["agent_count"] += 1
            if agent.status == "active":
                tenants[tenant_id]["active_agents"] += 1
            tenants[tenant_id]["agent_types"].add(agent.type)
        
        # Convert sets to lists for JSON serialization
        for tenant in tenants.values():
            tenant["agent_types"] = list(tenant["agent_types"])
        
        return jsonify({
            "tenants": list(tenants.values()),
            "total_tenants": len(tenants)
        })
        
    except Exception as e:
        logger.error(f"Error listing tenants: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500
