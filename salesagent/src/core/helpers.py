"""Helper functions for security, activity logging, and utilities."""

import time
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context

from src.core.audit_logger import get_audit_logger
from src.core.auth import get_principal_from_context
from src.core.database.database_session import get_db_session
from src.core.database.models import MediaBuy
from src.services.activity_feed import activity_feed


def _get_principal_id_from_context(context: Context) -> str:
    """Get principal ID from context with error handling."""
    principal_id = get_principal_from_context(context)
    if not principal_id:
        raise ToolError("Authentication required. Please provide valid credentials.")
    return principal_id


def _verify_principal(media_buy_id: str, context: Context):
    """Verify that the principal has access to the media buy."""
    principal_id = _get_principal_id_from_context(context)
    
    with get_db_session() as session:
        media_buy = session.query(MediaBuy).filter_by(media_buy_id=media_buy_id).first()
        if not media_buy:
            raise ToolError(f"Media buy {media_buy_id} not found")
        
        if media_buy.principal_id != principal_id:
            raise ToolError(f"Access denied to media buy {media_buy_id}")
    
    return principal_id


def log_tool_activity(context: Context, tool_name: str, start_time: float = None):
    """Log tool activity for audit and monitoring."""
    if start_time is None:
        start_time = time.time()
    
    principal_id = get_principal_from_context(context)
    if principal_id:
        # Log to activity feed
        activity_feed.log_activity(
            principal_id=principal_id,
            action=tool_name,
            details={"duration_ms": int((time.time() - start_time) * 1000)}
        )
        
        # Log to audit logger
        audit_logger = get_audit_logger()
        audit_logger.log_tool_usage(
            principal_id=principal_id,
            tool_name=tool_name,
            duration_ms=int((time.time() - start_time) * 1000)
        )


def validate_required_fields(data: dict, required_fields: list[str], field_type: str = "request"):
    """Validate that required fields are present in the data."""
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ToolError(f"Missing required {field_type} fields: {', '.join(missing_fields)}")


def safe_get_nested(data: dict, *keys, default=None):
    """Safely get nested dictionary values."""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def format_error_response(error: Exception, context: str = "") -> dict[str, Any]:
    """Format error response for consistent error handling."""
    return {
        "success": False,
        "error": str(error),
        "context": context,
        "timestamp": time.time()
    }

