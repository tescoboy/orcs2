"""
Utility functions and helpers for the main application.
Extracted from main.py to reduce file size and improve maintainability.
"""

import json
import logging
from typing import Any, Optional

from fastmcp.server.context import Context

import src.core.schemas as schemas
from src.core.config_loader import get_current_tenant
from src.core.database.database_session import get_db_session
from src.core.database.models import Principal as ModelPrincipal

logger = logging.getLogger(__name__)


def safe_parse_json_field(field_value, field_name="field", default=None):
    """
    Safely parse a database field that might be JSON string (SQLite) or dict (PostgreSQL JSONB).
    
    Args:
        field_value: The field value to parse
        field_name: Name of the field for error logging
        default: Default value if parsing fails
        
    Returns:
        Parsed value or default
    """
    if field_value is None:
        return default
    
    if isinstance(field_value, dict):
        return field_value
    
    if isinstance(field_value, str):
        try:
            return json.loads(field_value)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse {field_name} as JSON: {e}")
            return default
    
    return field_value


def get_principal_from_token(token: str, tenant_id: str) -> str | None:
    """Get principal ID from token."""
    try:
        with get_db_session() as session:
            principal = session.query(ModelPrincipal).filter_by(
                access_token=token, tenant_id=tenant_id
            ).first()
            return principal.principal_id if principal else None
    except Exception as e:
        logger.error(f"Error getting principal from token: {e}")
        return None


def get_principal_from_context(context: Context | None) -> str | None:
    """Get principal ID from context."""
    if not context or not hasattr(context, "headers"):
        return None
    
    token = context.headers.get("authorization")
    if not token:
        return None
    
    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    tenant = get_current_tenant()
    return get_principal_from_token(token, tenant["tenant_id"])


def get_principal_adapter_mapping(principal_id: str) -> dict[str, Any]:
    """Get adapter mapping for a principal."""
    with get_db_session() as session:
        principal = session.query(ModelPrincipal).filter_by(principal_id=principal_id).first()
        if not principal:
            return {}
        
        return safe_parse_json_field(principal.platform_mappings, "platform_mappings", {})


def get_principal_object(principal_id: str) -> schemas.Principal | None:
    """Get principal object from database."""
    with get_db_session() as session:
        principal = session.query(ModelPrincipal).filter_by(principal_id=principal_id).first()
        if not principal:
            return None
        
        return schemas.Principal(
            principal_id=principal.principal_id,
            tenant_id=principal.tenant_id,
            access_token=principal.access_token,
            platform_mappings=safe_parse_json_field(principal.platform_mappings, "platform_mappings", {}),
            created_at=principal.created_at,
            updated_at=principal.updated_at
        )


def get_adapter_principal_id(principal_id: str, adapter: str) -> str | None:
    """Get adapter-specific principal ID."""
    mapping = get_principal_adapter_mapping(principal_id)
    return mapping.get(adapter, {}).get("principal_id")
