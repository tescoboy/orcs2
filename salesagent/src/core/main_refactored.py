"""Refactored main.py - imports from modular files."""

import logging
import os

from fastmcp import FastMCP

# Import from modular files
from src.core.auth import (
    get_principal_from_context,
    get_principal_object
)
from src.core.adapters import get_adapter, get_adapter_principal_id
from src.core.initialization import (
    initialize_database,
    load_configuration,
    initialize_creative_engine,
    load_media_buys_from_db,
    media_buys,
    creative_assignments,
    creative_statuses
)
from src.core.helpers import (
    _get_principal_id_from_context,
    _verify_principal,
    log_tool_activity
)
from src.core.media_buy_tools import create_media_buy

# Import other modules that will be created
# from src.core.creative_tools import *
# from src.core.admin_tools import *
# from src.core.human_tasks import *
# from src.core.product_tools import *

logger = logging.getLogger(__name__)

# Initialize the system
initialize_database()
config = load_configuration()
creative_engine = initialize_creative_engine()
load_media_buys_from_db()

# Create MCP server
mcp = FastMCP(name="AdCPSalesAgent")

# Register tools from modules
@mcp.tool
def create_media_buy_tool(req, context):
    """Create a new media buy."""
    return create_media_buy(req, context)

# TODO: Implement these functions in media_buy_tools.py
# @mcp.tool
# def check_media_buy_status_tool(req, context):
#     """Check the status of a media buy."""
#     return check_media_buy_status(req, context)

# @mcp.tool
# def update_media_buy_tool(req, context):
#     """Update an existing media buy."""
#     return update_media_buy(req, context)

# @mcp.tool
# def get_media_buy_delivery_tool(req, context):
#     """Get delivery data for a specific media buy."""
#     return get_media_buy_delivery(req, context)

# @mcp.tool
# def get_all_media_buy_delivery_tool(req, context):
#     """Get delivery data for all media buys for a principal."""
#     return get_all_media_buy_delivery(req, context)

# TODO: Add more tool registrations as other modules are created
# @mcp.tool
# def add_creative_assets_tool(req, context):
#     return add_creative_assets(req, context)

# @mcp.tool
# def check_creative_status_tool(req, context):
#     return check_creative_status(req, context)

# @mcp.tool
# def approve_creative_tool(req, context):
#     return approve_creative(req, context)

# @mcp.tool
# def create_workflow_step_for_task_tool(req, context):
#     return create_workflow_step_for_task(req, context)

# @mcp.tool
# def get_pending_workflows_tool(req, context):
#     return get_pending_workflows(req, context)

# @mcp.tool
# def assign_task_tool(req, context):
#     return assign_task(req, context)

# @mcp.tool
# def complete_task_tool(req, context):
#     return complete_task(req, context)

# @mcp.tool
# def verify_task_tool(req, context):
#     return verify_task(req, context)

# @mcp.tool
# def get_product_catalog_tool(req, context):
#     return get_product_catalog()

# @mcp.tool
# def get_targeting_capabilities_tool(req, context):
#     return get_targeting_capabilities()

# @mcp.tool
# def check_aee_requirements_tool(req, context):
#     return check_aee_requirements(req, context)

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()

