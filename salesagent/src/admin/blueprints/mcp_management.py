"""
MCP Agent Management - Admin interface for MCP agents
"""
import logging
import asyncio
from typing import List, Dict, Any

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify

from src.services.agent_management_service import agent_management_service
from src.orchestrator.mcp_client import mcp_client
from src.core.schemas.agent import AgentStatus

logger = logging.getLogger(__name__)

# Create Blueprint
mcp_management_bp = Blueprint("mcp_management", __name__, url_prefix="/admin")


@mcp_management_bp.route("/mcp")
def list_mcp_agents():
    """List all MCP agents with management interface."""
    try:
        # Get all MCP agents
        mcp_agents_data = agent_management_service.discover_active_agents(
            agent_types=["mcp"]
        )
        
        # Prepare data for template
        mcp_agents = []
        for agent, tenant_id, tenant_name in mcp_agents_data:
            mcp_agents.append({
                'agent_id': agent.agent_id,
                'tenant_id': tenant_id,
                'tenant_name': tenant_name,
                'name': agent.name,
                'endpoint_url': agent.endpoint_url,
                'status': agent.status.value,
                'config': agent.config,
                'created_at': agent.created_at,
                'updated_at': agent.updated_at
            })
        
        return render_template("admin/mcp/list.html", mcp_agents=mcp_agents)
        
    except Exception as e:
        logger.error(f"Error loading MCP agents: {e}", exc_info=True)
        flash("Error loading MCP agents", "error")
        return redirect(url_for("core.index"))


@mcp_management_bp.route("/mcp/test/<tenant_id>/<agent_id>", methods=["POST"])
def test_mcp_agent(tenant_id: str, agent_id: str):
    """Test MCP agent connectivity and functionality."""
    try:
        # Get agent details
        agent = agent_management_service.get_agent_details(agent_id, tenant_id)
        
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        if agent.type != "mcp":
            return jsonify({"success": False, "error": "Agent is not an MCP agent"}), 400
        
        # Test MCP endpoint
        test_result = asyncio.run(mcp_client.test_mcp_endpoint(agent.endpoint_url))
        
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "test_result": test_result
        })
        
    except Exception as e:
        logger.error(f"Error testing MCP agent: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@mcp_management_bp.route("/mcp/create", methods=["GET", "POST"])
def create_mcp_agent():
    """Create a new MCP agent."""
    if request.method == "GET":
        # Get all tenants for the form
        tenants_data = agent_management_service.discover_active_agents()
        tenants = list(set((tenant_id, tenant_name) for _, tenant_id, tenant_name in tenants_data))
        tenants.sort(key=lambda x: x[1])  # Sort by tenant name
        
        return render_template("admin/mcp/create.html", tenants=tenants)
    
    try:
        # Get form data
        tenant_id = request.form.get("tenant_id", "").strip()
        agent_name = request.form.get("name", "").strip()
        endpoint_url = request.form.get("endpoint_url", "").strip()
        api_key = request.form.get("api_key", "").strip()
        timeout_seconds = int(request.form.get("timeout_seconds", "10"))
        
        if not all([tenant_id, agent_name, endpoint_url]):
            flash("Tenant ID, agent name, and endpoint URL are required", "error")
            return render_template("admin/mcp/create.html")
        
        # Generate agent ID
        agent_id = f"{tenant_id}_mcp_{agent_name.lower().replace(' ', '_')}"
        
        # Create agent configuration
        agent_config = {
            "name": agent_name,
            "type": "mcp",
            "status": "active",
            "endpoint_url": endpoint_url,
            "config": {
                "api_key": api_key,
                "timeout_seconds": timeout_seconds,
                "mcp_version": "1.0"
            }
        }
        
        # Add to tenant configuration
        success = agent_management_service.add_agent_to_tenant(tenant_id, agent_id, agent_config)
        
        if success:
            flash(f"MCP agent '{agent_name}' created successfully!", "success")
            return redirect(url_for("mcp_management.list_mcp_agents"))
        else:
            flash("Failed to create MCP agent", "error")
            return render_template("admin/mcp/create.html")
            
    except Exception as e:
        logger.error(f"Error creating MCP agent: {e}", exc_info=True)
        flash(f"Error creating MCP agent: {str(e)}", "error")
        return render_template("admin/mcp/create.html")


@mcp_management_bp.route("/mcp/<tenant_id>/<agent_id>/edit", methods=["GET", "POST"])
def edit_mcp_agent(tenant_id: str, agent_id: str):
    """Edit MCP agent configuration."""
    try:
        agent = agent_management_service.get_agent_details(agent_id, tenant_id)
        
        if not agent:
            flash("MCP agent not found", "error")
            return redirect(url_for("mcp_management.list_mcp_agents"))
        
        if request.method == "GET":
            return render_template("admin/mcp/edit.html", agent=agent)
        
        # Handle POST request
        agent_name = request.form.get("name", agent.name).strip()
        endpoint_url = request.form.get("endpoint_url", agent.endpoint_url).strip()
        api_key = request.form.get("api_key", "").strip()
        timeout_seconds = int(request.form.get("timeout_seconds", "10"))
        
        # Update agent configuration
        updated_config = agent.config.copy()
        updated_config.update({
            "api_key": api_key,
            "timeout_seconds": timeout_seconds
        })
        
        success = agent_management_service.update_agent_config(
            agent_id, tenant_id, {
                "name": agent_name,
                "endpoint_url": endpoint_url,
                "config": updated_config
            }
        )
        
        if success:
            flash(f"MCP agent '{agent_name}' updated successfully!", "success")
            return redirect(url_for("mcp_management.list_mcp_agents"))
        else:
            flash("Failed to update MCP agent", "error")
            return render_template("admin/mcp/edit.html", agent=agent)
            
    except Exception as e:
        logger.error(f"Error editing MCP agent: {e}", exc_info=True)
        flash(f"Error editing MCP agent: {str(e)}", "error")
        return redirect(url_for("mcp_management.list_mcp_agents"))


@mcp_management_bp.route("/mcp/<tenant_id>/<agent_id>/delete", methods=["POST"])
def delete_mcp_agent(tenant_id: str, agent_id: str):
    """Delete MCP agent."""
    try:
        success = agent_management_service.delete_agent(agent_id, tenant_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"MCP agent {agent_id} deleted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to delete MCP agent"
            }), 500
            
    except Exception as e:
        logger.error(f"Error deleting MCP agent: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@mcp_management_bp.route("/mcp/health")
def mcp_health_status():
    """Get health status of all MCP agents."""
    try:
        # Get all MCP agents
        mcp_agents_data = agent_management_service.discover_active_agents(
            agent_types=["mcp"]
        )
        
        health_results = []
        
        for agent, tenant_id, tenant_name in mcp_agents_data:
            try:
                # Test each MCP agent
                test_result = asyncio.run(mcp_client.test_mcp_endpoint(agent.endpoint_url))
                
                health_results.append({
                    "agent_id": agent.agent_id,
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "name": agent.name,
                    "endpoint_url": agent.endpoint_url,
                    "status": agent.status.value,
                    "health_status": test_result["status"],
                    "response_time_ms": test_result.get("response_time_ms", 0),
                    "message": test_result.get("message", "")
                })
                
            except Exception as e:
                health_results.append({
                    "agent_id": agent.agent_id,
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name,
                    "name": agent.name,
                    "endpoint_url": agent.endpoint_url,
                    "status": agent.status.value,
                    "health_status": "error",
                    "response_time_ms": 0,
                    "message": str(e)
                })
        
        return jsonify(health_results)
        
    except Exception as e:
        logger.error(f"Error getting MCP health status: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
