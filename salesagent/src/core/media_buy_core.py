"""
Core media buy operations (under 150 lines).
Extracted from media_buy_operations.py to maintain the 150-line limit.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Dict

from fastmcp import FastMCP
from fastmcp.server.context import Context

from src.core.adapters import get_adapter
from src.core.audit_logger import get_audit_logger
from src.core.config_loader import get_current_tenant
from src.core.context_manager import get_context_manager
from src.core.database.database_session import get_db_session
from src.core.database.models import MediaBuy
from src.core.schemas import (
    CreateMediaBuyRequest,
    CreateMediaBuyResponse,
    CheckMediaBuyStatusRequest,
    CheckMediaBuyStatusResponse,
)
from src.core.utils import get_principal_from_context, get_principal_object
from src.services.activity_feed import activity_feed

logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()

# Global context map for tracking media buys
context_map: Dict[str, str] = {}


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
def create_media_buy(req: CreateMediaBuyRequest, context: Context) -> CreateMediaBuyResponse:
    """Create a new media buy."""
    start_time = time.time()
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    # Context management - only needed for async operations
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
            step_type="create_media_buy",
            step_data={
                "request": req.dict(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Get adapter
        adapter = get_adapter(principal, dry_run=req.dry_run)

        # Create media buy
        media_buy_id = str(uuid.uuid4())
        context_id = str(uuid.uuid4())
        
        # Store in context map for quick lookup
        context_map[context_id] = media_buy_id

        # Create media buy in database
        with get_db_session() as session:
            media_buy = MediaBuy(
                media_buy_id=media_buy_id,
                context_id=context_id,
                principal_id=principal_id,
                tenant_id=tenant["tenant_id"],
                status="pending",
                total_budget=req.total_budget,
                targeting_overlay=req.targeting_overlay,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(media_buy)
            session.commit()

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="create_media_buy",
            details={
                "media_buy_id": media_buy_id,
                "total_budget": req.total_budget,
                "dry_run": req.dry_run,
            },
        )

        # Update workflow step
        ctx_manager.update_workflow_step(
            step_id=step.step_id,
            status="completed",
            result_data={
                "media_buy_id": media_buy_id,
                "context_id": context_id,
                "status": "pending",
            },
        )

        log_tool_activity(context, "create_media_buy", start_time)

        return CreateMediaBuyResponse(
            media_buy_id=media_buy_id,
            context_id=context_id,
            status="pending",
            message="Media buy created successfully",
        )

    except Exception as e:
        logger.error(f"Error creating media buy: {e}")
        
        # Update workflow step with error
        if step:
            ctx_manager.update_workflow_step(
                step_id=step.step_id,
                status="failed",
                error_data={"error": str(e)},
            )
        
        raise


@FastMCP.tool
def check_media_buy_status(req: CheckMediaBuyStatusRequest, context: Context) -> CheckMediaBuyStatusResponse:
    """Check the status of a media buy using the context_id returned from create_media_buy."""
    _get_principal_id_from_context(context)

    # Get the media_buy_id from context_id
    media_buy_id = None
    if req.context_id in context_map:
        media_buy_id = context_map[req.context_id]

    # If not in memory, check database
    if not media_buy_id:
        with get_db_session() as session:
            media_buy = session.query(MediaBuy).filter_by(context_id=req.context_id).first()
            if media_buy:
                media_buy_id = media_buy.media_buy_id

    if not media_buy_id:
        raise ValueError(f"No media buy found for context_id {req.context_id}")

    # Get media buy from database
    with get_db_session() as session:
        media_buy = session.query(MediaBuy).filter_by(media_buy_id=media_buy_id).first()
        if not media_buy:
            raise ValueError(f"Media buy {media_buy_id} not found")

        return CheckMediaBuyStatusResponse(
            media_buy_id=media_buy_id,
            context_id=req.context_id,
            status=media_buy.status,
            total_budget=media_buy.total_budget,
            targeting_overlay=media_buy.targeting_overlay,
            created_at=media_buy.created_at,
            updated_at=media_buy.updated_at,
        )
