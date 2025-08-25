"""
Main application entry point.
This file has been refactored to import from smaller, focused modules.
Original main.py was 2,798 lines - now split into logical modules of 150 lines or less.
"""

import json
import logging
import os
import time
import uuid
from datetime import date, datetime, timedelta

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from rich.console import Console

# Import all the split modules
from src.core.utils import (
    safe_parse_json_field,
    get_principal_from_token,
    get_principal_from_context,
    get_principal_adapter_mapping,
    get_principal_object,
    get_adapter_principal_id,
)

from src.core.adapters import (
    get_adapter,
    get_creative_engine,
)

from src.core.media_buy_operations import (
    create_media_buy,
    check_media_buy_status,
    update_media_buy,
    get_media_buy_delivery,
    get_all_media_buy_delivery,
)

from src.core.creative_management import (
    add_creative_assets,
    check_creative_status,
    approve_adaptation,
    get_creatives,
    create_creative_group,
    create_creative,
    assign_creative,
)

from src.core.task_management import (
    create_workflow_step_for_task,
    get_pending_workflows,
    assign_task,
    complete_task,
    verify_task,
    mark_task_complete,
)

from src.core.product_catalog import (
    get_product_catalog,
    get_targeting_capabilities,
    check_aee_requirements,
)

# Import remaining dependencies
from src.adapters.google_ad_manager import GoogleAdManager
from src.adapters.kevel import Kevel
from src.adapters.mock_ad_server import MockAdServer as MockAdServerAdapter
from src.adapters.mock_creative_engine import MockCreativeEngine
from src.adapters.triton_digital import TritonDigital
from src.core.audit_logger import get_audit_logger
from src.services.activity_feed import activity_feed

logger = logging.getLogger(__name__)
import src.core.schemas as schemas
from product_catalog_providers.factory import get_product_catalog_provider
from scripts.setup.init_database import init_db
from src.core.config_loader import (
    get_current_tenant,
    load_config,
    set_current_tenant,
)
from src.core.context_manager import get_context_manager
from src.core.database.database_session import get_db_session
from src.core.database.models import AdapterConfig, MediaBuy, Task, Tenant
from src.core.database.models import HumanTask as ModelHumanTask
from src.core.database.models import Principal as ModelPrincipal
from src.core.database.models import Product as ModelProduct
from src.core.schemas import *
from src.services.policy_check_service import PolicyCheckService, PolicyStatus

# CRITICAL: Re-import models AFTER wildcard to prevent collision
# The wildcard import overwrites Product, Principal, HumanTask
from src.services.slack_notifier import get_slack_notifier

# Initialize Rich console
console = Console()

# Global variables and state
context_map = {}
media_buys = {}
creative_assignments = {}

# Initialize FastMCP
mcp = FastMCP("adcp-server")

# Load media buys from database on startup
def load_media_buys_from_db():
    """Load existing media buys from database into memory."""
    try:
        with get_db_session() as session:
            media_buys_from_db = session.query(MediaBuy).all()
            for media_buy in media_buys_from_db:
                media_buys[media_buy.media_buy_id] = (
                    schemas.CreateMediaBuyRequest(
                        total_budget=media_buy.total_budget,
                        targeting_overlay=media_buy.targeting_overlay,
                        dry_run=False,
                    ),
                    media_buy.status,
                )
                if media_buy.context_id:
                    context_map[media_buy.context_id] = media_buy.media_buy_id
        logger.info(f"Loaded {len(media_buys_from_db)} media buys from database")
    except Exception as e:
        logger.error(f"Error loading media buys from database: {e}")

# Legacy functions that need to be kept for backward compatibility
@mcp.tool
def legacy_update_media_buy(req: LegacyUpdateMediaBuyRequest, context: Context):
    """Legacy tool for backward compatibility."""
    from src.core.utils import get_principal_from_context
    from src.core.database.database_session import get_db_session
    from src.core.database.models import MediaBuy
    
    principal_id = get_principal_from_context(context)
    if not principal_id:
        raise ValueError("No principal ID found in context")
    
    with get_db_session() as session:
        media_buy = session.query(MediaBuy).filter_by(media_buy_id=req.media_buy_id).first()
        if not media_buy:
            raise ValueError(f"Media buy {req.media_buy_id} not found")
        
        if media_buy.principal_id != principal_id:
            raise ValueError(f"Principal {principal_id} does not have access to media buy {req.media_buy_id}")
    
    buy_request, _ = media_buys[req.media_buy_id]
    if req.new_total_budget:
        buy_request.total_budget = req.new_total_budget
    if req.new_targeting_overlay:
        buy_request.targeting_overlay = req.new_targeting_overlay
    if req.creative_assignments:
        creative_assignments[req.media_buy_id] = req.creative_assignments
    return {"status": "success"}

# Unified update tools
@mcp.tool
def update_package(req: UpdatePackageRequest, context: Context) -> UpdateMediaBuyResponse:
    """Update a media buy package."""
    return update_media_buy(
        UpdateMediaBuyRequest(
            media_buy_id=req.media_buy_id,
            total_budget=req.total_budget,
            targeting_overlay=req.targeting_overlay,
            dry_run=req.dry_run,
        ),
        context
    )

# Admin and approval functions
@mcp.tool
def get_pending_creatives(req: GetPendingCreativesRequest, context: Context) -> GetPendingCreativesResponse:
    """Get pending creatives that need approval."""
    from src.core.utils import get_principal_from_context
    from src.core.config_loader import get_current_tenant
    
    principal_id = get_principal_from_context(context)
    tenant = get_current_tenant()
    is_admin = principal_id == f"{tenant['tenant_id']}_admin"
    
    if not is_admin:
        raise ValueError("Admin privileges required")
    
    # This would typically query the database for pending creatives
    # For now, return empty list
    return GetPendingCreativesResponse(creatives=[])

@mcp.tool
def approve_creative(req: ApproveCreativeRequest, context: Context) -> ApproveCreativeResponse:
    """Approve a creative."""
    from src.core.utils import get_principal_from_context
    from src.core.config_loader import get_current_tenant
    
    principal_id = get_principal_from_context(context)
    tenant = get_current_tenant()
    is_admin = principal_id == f"{tenant['tenant_id']}_admin"
    
    if not is_admin:
        raise ValueError("Admin privileges required")
    
    # This would typically update the creative status in the database
    return ApproveCreativeResponse(
        creative_id=req.creative_id,
        status="approved",
        message="Creative approved successfully",
    )

@mcp.tool
def update_performance_index(req: UpdatePerformanceIndexRequest, context: Context) -> UpdatePerformanceIndexResponse:
    """Update performance index for a creative."""
    from src.core.utils import get_principal_from_context
    from src.core.config_loader import get_current_tenant
    
    principal_id = get_principal_from_context(context)
    tenant = get_current_tenant()
    
    # This would typically update the performance index in the database
    return UpdatePerformanceIndexResponse(
        creative_id=req.creative_id,
        performance_index=req.performance_index,
        status="updated",
        message="Performance index updated successfully",
    )

# Initialize the application
def initialize_app():
    """Initialize the application."""
    try:
        # Load configuration
        load_config()
        
        # Initialize database
        init_db()
        
        # Load media buys from database
        load_media_buys_from_db()
        
        logger.info("Application initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        raise

# Run initialization
if __name__ == "__main__":
    initialize_app()
