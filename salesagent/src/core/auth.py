"""Authentication and principal management functions."""

import json
import logging
from typing import Any

from fastmcp.server.context import Context

from src.core.config_loader import get_current_tenant, set_current_tenant
from src.core.database.database_session import get_db_session
from src.core.database.models import Principal as ModelPrincipal, Tenant
import src.core.schemas as schemas

logger = logging.getLogger(__name__)


def safe_parse_json_field(field_value, field_name="field", default=None):
    """Safely parse a database field that might be JSON string or dict."""
    if not field_value:
        return default if default is not None else {}

    if isinstance(field_value, str):
        try:
            parsed = json.loads(field_value)
            if default is not None and not isinstance(parsed, type(default)):
                logger.warning(f"Parsed {field_name} has unexpected type: {type(parsed)}, expected {type(default)}")
                return default
            return parsed
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Invalid JSON in {field_name}: {e}")
            return default if default is not None else {}
    elif isinstance(field_value, dict | list):
        return field_value
    else:
        logger.warning(f"Unexpected type for {field_name}: {type(field_value)}")
        return default if default is not None else {}


def get_principal_from_token(token: str, tenant_id: str) -> str | None:
    """Looks up a principal_id from the database using a token."""
    tenant = get_current_tenant()
    if tenant and token == tenant.get("admin_token"):
        return f"{tenant['tenant_id']}_admin"

    with get_db_session() as session:
        principal = session.query(ModelPrincipal).filter_by(access_token=token, tenant_id=tenant_id).first()
        return principal.principal_id if principal else None


def get_principal_from_context(context: Context | None) -> str | None:
    """Extract principal ID from the FastMCP context using x-adcp-auth header."""
    if not context:
        return None

    try:
        request = context.get_http_request()
        if not request:
            return None

        tenant_id = request.headers.get("x-adcp-tenant")
        if not tenant_id:
            host = request.headers.get("host", "")
            subdomain = host.split(".")[0] if "." in host else None
            if subdomain and subdomain != "localhost":
                tenant_id = subdomain

        if not tenant_id:
            tenant_id = "default"

        with get_db_session() as session:
            tenant = session.query(Tenant).filter_by(tenant_id=tenant_id, is_active=True).first()
            if not tenant:
                print(f"No active tenant found for ID: {tenant_id}")
                return None

            tenant_dict = {
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "subdomain": tenant.subdomain,
                "ad_server": tenant.ad_server,
                "max_daily_budget": tenant.max_daily_budget,
                "enable_aee_signals": tenant.enable_aee_signals,
                "authorized_emails": tenant.authorized_emails or [],
                "authorized_domains": tenant.authorized_domains or [],
                "slack_webhook_url": tenant.slack_webhook_url,
                "admin_token": tenant.admin_token,
                "auto_approve_formats": tenant.auto_approve_formats or [],
                "human_review_required": tenant.human_review_required,
                "slack_audit_webhook_url": tenant.slack_audit_webhook_url,
                "hitl_webhook_url": tenant.hitl_webhook_url,
                "policy_settings": tenant.policy_settings,
            }
        set_current_tenant(tenant_dict)

        auth_token = request.headers.get("x-adcp-auth")
        if not auth_token:
            return None

        return get_principal_from_token(auth_token, tenant_dict["tenant_id"])
    except Exception as e:
        print(f"Auth error: {e}")
        return None


def get_principal_adapter_mapping(principal_id: str) -> dict[str, Any]:
    """Get the platform mappings for a principal."""
    tenant = get_current_tenant()
    with get_db_session() as session:
        principal = (
            session.query(ModelPrincipal).filter_by(principal_id=principal_id, tenant_id=tenant["tenant_id"]).first()
        )
        return principal.platform_mappings if principal else {}


def get_principal_object(principal_id: str) -> schemas.Principal | None:
    """Get a Principal object for the given principal_id."""
    tenant = get_current_tenant()
    with get_db_session() as session:
        principal = (
            session.query(ModelPrincipal).filter_by(principal_id=principal_id, tenant_id=tenant["tenant_id"]).first()
        )

        if principal:
            return schemas.Principal(
                principal_id=principal.principal_id,
                name=principal.name,
                platform_mappings=principal.platform_mappings,
            )
    return None
