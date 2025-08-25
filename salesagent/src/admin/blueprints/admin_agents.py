"""
Admin agent management blueprint for viewing and managing agents across tenants
"""
import logging
from typing import List, Tuple

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify

from src.services.agent_management_service import agent_management_service
from src.core.schemas.agent import AgentConfig, AgentStatus

logger = logging.getLogger(__name__)

# Create Blueprint
admin_agents_bp = Blueprint("admin_agents", __name__, url_prefix="/admin")


@admin_agents_bp.route("/agents")
def list_agents():
    """List all agents across tenants with admin interface."""
    try:
        # Get filter parameters
        include_tenant_ids = request.args.getlist('include_tenant_ids')
        exclude_tenant_ids = request.args.getlist('exclude_tenant_ids')
        agent_types = request.args.getlist('agent_types')
        status_filter = request.args.get('status')
        
        # Convert empty lists to None for the service
        include_tenant_ids = include_tenant_ids if include_tenant_ids else None
        exclude_tenant_ids = exclude_tenant_ids if exclude_tenant_ids else None
        agent_types = agent_types if agent_types else None
        
        # Get agents
        agents_data = agent_management_service.discover_active_agents(
            include_tenant_ids=include_tenant_ids,
            exclude_tenant_ids=exclude_tenant_ids,
            agent_types=agent_types
        )
        
        # Get statistics
        stats = agent_management_service.get_agent_statistics()
        
        # Prepare data for template
        agents_list = []
        for agent, tenant_id, tenant_name in agents_data:
            agents_list.append({
                'agent_id': agent.agent_id,
                'tenant_id': tenant_id,
                'tenant_name': tenant_name,
                'name': agent.name,
                'type': agent.type,
                'status': agent.status.value,
                'endpoint_url': agent.endpoint_url,
                'created_at': agent.created_at,
                'updated_at': agent.updated_at
            })
        
        return render_template(
            "admin/agents/list.html",
            agents=agents_list,
            stats=stats,
            filters={
                'include_tenant_ids': include_tenant_ids or [],
                'exclude_tenant_ids': exclude_tenant_ids or [],
                'agent_types': agent_types or [],
                'status': status_filter
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading agents: {e}", exc_info=True)
        flash("Error loading agents", "error")
        return redirect(url_for("core.index"))


@admin_agents_bp.route("/agents/<tenant_id>/<agent_id>")
def view_agent(tenant_id: str, agent_id: str):
    """View agent details."""
    try:
        agent = agent_management_service.get_agent_details(agent_id, tenant_id)
        
        if not agent:
            flash("Agent not found", "error")
            return redirect(url_for("admin_agents.list_agents"))
        
        return render_template("admin/agents/view.html", agent=agent)
        
    except Exception as e:
        logger.error(f"Error loading agent: {e}", exc_info=True)
        flash("Error loading agent", "error")
        return redirect(url_for("admin_agents.list_agents"))


@admin_agents_bp.route("/agents/<tenant_id>/<agent_id>/toggle", methods=["POST"])
def toggle_agent(tenant_id: str, agent_id: str):
    """Toggle agent status between active and inactive."""
    try:
        agent = agent_management_service.get_agent_details(agent_id, tenant_id)
        
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        
        # Toggle status
        new_status = AgentStatus.INACTIVE if agent.status == AgentStatus.ACTIVE else AgentStatus.ACTIVE
        
        success = agent_management_service.update_agent_status(agent_id, tenant_id, new_status)
        
        if success:
            return jsonify({
                "success": True,
                "new_status": new_status.value,
                "message": f"Agent {agent_id} status updated to {new_status.value}"
            })
        else:
            return jsonify({"success": False, "error": "Failed to update agent status"}), 500
            
    except Exception as e:
        logger.error(f"Error toggling agent status: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@admin_agents_bp.route("/agents/statistics")
def agent_statistics():
    """Get agent statistics as JSON."""
    try:
        stats = agent_management_service.get_agent_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting agent statistics: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@admin_agents_bp.route("/performance")
def performance_dashboard():
    """Performance monitoring dashboard"""
    return render_template('admin/performance/dashboard.html')


@admin_agents_bp.route("/agents/tenants")
def list_tenants_with_agents():
    """List all tenants that have agents."""
    try:
        # Get all agents to extract unique tenants
        all_agents = agent_management_service.discover_active_agents()
        
        # Group by tenant
        tenants = {}
        for agent, tenant_id, tenant_name in all_agents:
            if tenant_id not in tenants:
                tenants[tenant_id] = {
                    'tenant_id': tenant_id,
                    'tenant_name': tenant_name,
                    'agent_count': 0,
                    'active_agents': 0,
                    'agent_types': set()
                }
            
            tenants[tenant_id]['agent_count'] += 1
            if agent.status == AgentStatus.ACTIVE:
                tenants[tenant_id]['active_agents'] += 1
            tenants[tenant_id]['agent_types'].add(agent.type)
        
        # Convert sets to lists for JSON serialization
        for tenant in tenants.values():
            tenant['agent_types'] = list(tenant['agent_types'])
        
        return jsonify(list(tenants.values()))
        
    except Exception as e:
        logger.error(f"Error listing tenants with agents: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
