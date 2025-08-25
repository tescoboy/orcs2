"""
Core creative management operations (under 150 lines).
Extracted from creative_management.py to maintain the 150-line limit.
"""

import logging
import time
import uuid
from datetime import datetime

from fastmcp import FastMCP
from fastmcp.server.context import Context

from src.core.adapters import get_creative_engine
from src.core.audit_logger import get_audit_logger
from src.core.config_loader import get_current_tenant
from src.core.context_manager import get_context_manager
from src.core.database.database_session import get_db_session
from src.core.database.models import MediaBuy
from src.core.schemas import (
    AddCreativeAssetsRequest,
    AddCreativeAssetsResponse,
    CheckCreativeStatusRequest,
    CheckCreativeStatusResponse,
    ApproveAdaptationRequest,
    ApproveAdaptationResponse,
)
from src.core.utils import get_principal_from_context, get_principal_object
from src.services.activity_feed import activity_feed

logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()


def _get_principal_id_from_context(context: Context) -> str:
    """Get principal ID from context."""
    principal_id = get_principal_from_context(context)
    if not principal_id:
        raise ValueError("No principal ID found in context")
    return principal_id


def _verify_principal(media_buy_id: str, context: Context):
    """Verify that the principal has access to the media buy."""
    principal_id = _get_principal_id_from_context(context)
    
    with get_db_session() as session:
        media_buy = session.query(MediaBuy).filter_by(media_buy_id=media_buy_id).first()
        if not media_buy:
            raise ValueError(f"Media buy {media_buy_id} not found")
        
        if media_buy.principal_id != principal_id:
            raise ValueError(f"Principal {principal_id} does not have access to media buy {media_buy_id}")


def log_tool_activity(context: Context, tool_name: str, start_time: float = None):
    """Log tool activity for audit purposes."""
    if start_time is None:
        start_time = time.time()
    
    duration = time.time() - start_time
    principal_id = get_principal_from_context(context)
    tenant = get_current_tenant()
    
    audit_logger.log_activity(
        tenant_id=tenant["tenant_id"],
        principal_id=principal_id,
        action=tool_name,
        duration=duration,
        status="success"
    )


@FastMCP.tool
def add_creative_assets(req: AddCreativeAssetsRequest, context: Context) -> AddCreativeAssetsResponse:
    """Add creative assets to a media buy."""
    _verify_principal(req.media_buy_id, context)
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    # Create or get persistent context
    ctx_manager = get_context_manager()
    ctx_id = context.headers.get("x-context-id") if hasattr(context, "headers") else None
    persistent_ctx = None
    step = None

    # Get the Principal object
    principal = get_principal_object(principal_id)
    if not principal:
        raise ValueError(f"Principal {principal_id} not found")

    try:
        # Create or get persistent context
        persistent_ctx = ctx_manager.get_or_create_context(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            context_id=ctx_id,
            session_type="interactive",
        )

        # Create workflow step for this tool call
        step = ctx_manager.create_workflow_step(
            context_id=persistent_ctx.context_id,
            step_type="add_creative_assets",
            step_data={
                "request": req.dict(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Get creative engine
        creative_engine = get_creative_engine(principal, dry_run=req.dry_run)

        # Add creative assets
        creative_assets = []
        for asset in req.creative_assets:
            asset_id = str(uuid.uuid4())
            creative_assets.append({
                "asset_id": asset_id,
                "name": asset.name,
                "type": asset.type,
                "url": asset.url,
                "size": asset.size,
                "format": asset.format,
            })

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="add_creative_assets",
            details={
                "media_buy_id": req.media_buy_id,
                "creative_assets": creative_assets,
                "dry_run": req.dry_run,
            },
        )

        # Update workflow step
        ctx_manager.update_workflow_step(
            step_id=step.step_id,
            status="completed",
            result_data={
                "creative_assets": creative_assets,
                "status": "pending",
            },
        )

        return AddCreativeAssetsResponse(
            media_buy_id=req.media_buy_id,
            creative_assets=creative_assets,
            status="pending",
            message="Creative assets added successfully",
        )

    except Exception as e:
        logger.error(f"Error adding creative assets: {e}")
        
        # Update workflow step with error
        if step:
            ctx_manager.update_workflow_step(
                step_id=step.step_id,
                status="failed",
                error_data={"error": str(e)},
            )
        
        raise


@FastMCP.tool
def check_creative_status(req: CheckCreativeStatusRequest, context: Context) -> CheckCreativeStatusResponse:
    """Check the status of creative assets."""
    _verify_principal(req.media_buy_id, context)
    principal_id = _get_principal_id_from_context(context)

    # Get the Principal object
    principal = get_principal_object(principal_id)
    if not principal:
        raise ValueError(f"Principal {principal_id} not found")

    # Get creative engine
    creative_engine = get_creative_engine(principal, dry_run=False)

    try:
        # Check creative status
        status_data = creative_engine.check_creative_status(req.creative_asset_ids)
        
        return CheckCreativeStatusResponse(
            media_buy_id=req.media_buy_id,
            creative_asset_ids=req.creative_asset_ids,
            status_data=status_data,
        )

    except Exception as e:
        logger.error(f"Error checking creative status: {e}")
        raise


@FastMCP.tool
def approve_adaptation(req: ApproveAdaptationRequest, context: Context) -> ApproveAdaptationResponse:
    """Approve a creative adaptation."""
    _verify_principal(req.media_buy_id, context)
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    # Get the Principal object
    principal = get_principal_object(principal_id)
    if not principal:
        raise ValueError(f"Principal {principal_id} not found")

    # Get creative engine
    creative_engine = get_creative_engine(principal, dry_run=req.dry_run)

    try:
        # Approve adaptation
        new_creative_id = str(uuid.uuid4())
        result = creative_engine.approve_adaptation(
            adaptation_id=req.adaptation_id,
            approval_notes=req.approval_notes,
        )

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="approve_adaptation",
            details={
                "media_buy_id": req.media_buy_id,
                "adaptation_id": req.adaptation_id,
                "new_creative_id": new_creative_id,
                "dry_run": req.dry_run,
            },
        )

        return ApproveAdaptationResponse(
            media_buy_id=req.media_buy_id,
            adaptation_id=req.adaptation_id,
            new_creative_id=new_creative_id,
            status="approved",
            message=f"Adaptation approved and creative '{new_creative_id}' generated",
        )

    except Exception as e:
        logger.error(f"Error approving adaptation: {e}")
        raise
