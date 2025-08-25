"""
Creative operations (under 150 lines).
Extracted from creative_management.py to maintain the 150-line limit.
"""

import logging
import uuid
from datetime import datetime

from fastmcp import FastMCP
from fastmcp.server.context import Context

from src.core.adapters import get_creative_engine
from src.core.audit_logger import get_audit_logger
from src.core.config_loader import get_current_tenant
from src.core.database.database_session import get_db_session
from src.core.database.models import MediaBuy
from src.core.schemas import (
    GetCreativesRequest,
    GetCreativesResponse,
    CreateCreativeGroupRequest,
    CreateCreativeGroupResponse,
    CreateCreativeRequest,
    CreateCreativeResponse,
    AssignCreativeRequest,
    AssignCreativeResponse,
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


@FastMCP.tool
def get_creatives(req: GetCreativesRequest, context: Context) -> GetCreativesResponse:
    """Get creatives for a media buy."""
    _verify_principal(req.media_buy_id, context)
    principal_id = _get_principal_id_from_context(context)

    # Get the Principal object
    principal = get_principal_object(principal_id)
    if not principal:
        raise ValueError(f"Principal {principal_id} not found")

    # Get creative engine
    creative_engine = get_creative_engine(principal, dry_run=False)

    try:
        # Get creatives
        creatives = creative_engine.get_creatives(req.media_buy_id)
        
        return GetCreativesResponse(
            media_buy_id=req.media_buy_id,
            creatives=creatives,
        )

    except Exception as e:
        logger.error(f"Error getting creatives: {e}")
        raise


@FastMCP.tool
def create_creative_group(req: CreateCreativeGroupRequest, context: Context) -> CreateCreativeGroupResponse:
    """Create a creative group."""
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    # Get the Principal object
    principal = get_principal_object(principal_id)
    if not principal:
        raise ValueError(f"Principal {principal_id} not found")

    # Get creative engine
    creative_engine = get_creative_engine(principal, dry_run=req.dry_run)

    try:
        # Create creative group
        group_id = str(uuid.uuid4())
        result = creative_engine.create_creative_group(
            name=req.name,
            description=req.description,
            creative_ids=req.creative_ids,
        )

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="create_creative_group",
            details={
                "group_id": group_id,
                "name": req.name,
                "dry_run": req.dry_run,
            },
        )

        return CreateCreativeGroupResponse(
            group_id=group_id,
            name=req.name,
            status="created",
            message="Creative group created successfully",
        )

    except Exception as e:
        logger.error(f"Error creating creative group: {e}")
        raise


@FastMCP.tool
def create_creative(req: CreateCreativeRequest, context: Context) -> CreateCreativeResponse:
    """Create a new creative."""
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    # Get the Principal object
    principal = get_principal_object(principal_id)
    if not principal:
        raise ValueError(f"Principal {principal_id} not found")

    # Get creative engine
    creative_engine = get_creative_engine(principal, dry_run=req.dry_run)

    try:
        # Create creative
        creative_id = str(uuid.uuid4())
        result = creative_engine.create_creative(
            name=req.name,
            description=req.description,
            format=req.format,
            size=req.size,
            content=req.content,
        )

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="create_creative",
            details={
                "creative_id": creative_id,
                "name": req.name,
                "dry_run": req.dry_run,
            },
        )

        return CreateCreativeResponse(
            creative_id=creative_id,
            name=req.name,
            status="created",
            message="Creative created successfully",
        )

    except Exception as e:
        logger.error(f"Error creating creative: {e}")
        raise


@FastMCP.tool
def assign_creative(req: AssignCreativeRequest, context: Context) -> AssignCreativeResponse:
    """Assign a creative to a media buy."""
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
        # Assign creative
        result = creative_engine.assign_creative(
            media_buy_id=req.media_buy_id,
            creative_id=req.creative_id,
            assignment_type=req.assignment_type,
        )

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="assign_creative",
            details={
                "media_buy_id": req.media_buy_id,
                "creative_id": req.creative_id,
                "assignment_type": req.assignment_type,
                "dry_run": req.dry_run,
            },
        )

        return AssignCreativeResponse(
            media_buy_id=req.media_buy_id,
            creative_id=req.creative_id,
            status="assigned",
            message="Creative assigned successfully",
        )

    except Exception as e:
        logger.error(f"Error assigning creative: {e}")
        raise
