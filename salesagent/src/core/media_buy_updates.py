"""
Media buy update operations (under 150 lines).
Extracted from media_buy_operations.py to maintain the 150-line limit.
"""

import logging
import time
from datetime import datetime

from fastmcp import FastMCP
from fastmcp.server.context import Context

from src.core.adapters import get_adapter
from src.core.audit_logger import get_audit_logger
from src.core.config_loader import get_current_tenant
from src.core.database.database_session import get_db_session
from src.core.database.models import MediaBuy
from src.core.schemas import (
    UpdateMediaBuyRequest,
    UpdateMediaBuyResponse,
    GetMediaBuyDeliveryRequest,
    GetMediaBuyDeliveryResponse,
    GetAllMediaBuyDeliveryRequest,
    GetAllMediaBuyDeliveryResponse,
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
def update_media_buy(req: UpdateMediaBuyRequest, context: Context) -> UpdateMediaBuyResponse:
    """Update an existing media buy."""
    start_time = time.time()
    _verify_principal(req.media_buy_id, context)
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    try:
        # Get the Principal object
        principal = get_principal_object(principal_id)
        if not principal:
            raise ValueError(f"Principal {principal_id} not found")

        # Get adapter
        adapter = get_adapter(principal, dry_run=req.dry_run)

        # Update media buy in database
        with get_db_session() as session:
            media_buy = session.query(MediaBuy).filter_by(media_buy_id=req.media_buy_id).first()
            if not media_buy:
                raise ValueError(f"Media buy {req.media_buy_id} not found")

            # Update fields if provided
            if req.total_budget is not None:
                media_buy.total_budget = req.total_budget
            if req.targeting_overlay is not None:
                media_buy.targeting_overlay = req.targeting_overlay
            if req.status is not None:
                media_buy.status = req.status

            media_buy.updated_at = datetime.utcnow()
            session.commit()

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="update_media_buy",
            details={
                "media_buy_id": req.media_buy_id,
                "updates": req.dict(exclude_unset=True),
                "dry_run": req.dry_run,
            },
        )

        log_tool_activity(context, "update_media_buy", start_time)

        return UpdateMediaBuyResponse(
            media_buy_id=req.media_buy_id,
            status="success",
            message="Media buy updated successfully",
        )

    except Exception as e:
        logger.error(f"Error updating media buy: {e}")
        raise


@FastMCP.tool
def get_media_buy_delivery(req: GetMediaBuyDeliveryRequest, context: Context) -> GetMediaBuyDeliveryResponse:
    """Get delivery data for a specific media buy."""
    _verify_principal(req.media_buy_id, context)
    principal_id = _get_principal_id_from_context(context)

    # Get the Principal object
    principal = get_principal_object(principal_id)
    if not principal:
        raise ValueError(f"Principal {principal_id} not found")

    # Get adapter
    adapter = get_adapter(principal, dry_run=False)

    try:
        # Get delivery data from adapter
        delivery_data = adapter.get_delivery_data(req.media_buy_id)
        
        return GetMediaBuyDeliveryResponse(
            media_buy_id=req.media_buy_id,
            delivery_data=delivery_data,
        )

    except Exception as e:
        logger.error(f"Error getting delivery data: {e}")
        raise


@FastMCP.tool
def get_all_media_buy_delivery(req: GetAllMediaBuyDeliveryRequest, context: Context) -> GetAllMediaBuyDeliveryResponse:
    """Get delivery data for all media buys for a principal."""
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    # Get the Principal object
    principal = get_principal_object(principal_id)
    if not principal:
        raise ValueError(f"Principal {principal_id} not found")

    # Get adapter
    adapter = get_adapter(principal, dry_run=False)

    try:
        # Get all delivery data from adapter
        all_delivery_data = adapter.get_all_delivery_data()
        
        return GetAllMediaBuyDeliveryResponse(
            principal_id=principal_id,
            delivery_data=all_delivery_data,
        )

    except Exception as e:
        logger.error(f"Error getting all delivery data: {e}")
        raise
