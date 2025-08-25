"""Media buy related MCP tools."""

import time
from datetime import datetime
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context

from src.core.auth import get_principal_object
from src.core.adapters import get_adapter
from src.core.config_loader import get_current_tenant
from src.core.database.database_session import get_db_session
from src.core.database.models import MediaBuy, Principal as ModelPrincipal
from src.core.helpers import _get_principal_id_from_context, log_tool_activity
from src.core.initialization import media_buys, creative_statuses
from src.core.schemas import (
    CreateMediaBuyRequest, CreateMediaBuyResponse, MediaPackage, CreativeStatus
)
from src.services.activity_feed import activity_feed

# Global variables (will be imported from initialization)
DRY_RUN_MODE = False


def create_media_buy(req: CreateMediaBuyRequest, context: Context) -> CreateMediaBuyResponse:
    """Create a new media buy."""
    start_time = time.time()
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    # Get the Principal object
    principal = get_principal_object(principal_id)
    if not principal:
        error_msg = f"Principal {principal_id} not found"
        raise ToolError(error_msg)

    # Validate targeting doesn't use managed-only dimensions
    if req.targeting_overlay:
        from targeting_capabilities import validate_overlay_targeting
        violations = validate_overlay_targeting(req.targeting_overlay.model_dump(exclude_none=True))
        if violations:
            error_msg = f"Targeting validation failed: {'; '.join(violations)}"
            raise ToolError(error_msg)

    # Get the appropriate adapter
    adapter = get_adapter(principal, dry_run=DRY_RUN_MODE)

    # Check if manual approval is required
    manual_approval_required = (
        adapter.manual_approval_required if hasattr(adapter, "manual_approval_required") else False
    )
    manual_approval_operations = (
        adapter.manual_approval_operations if hasattr(adapter, "manual_approval_operations") else []
    )

    # Check if auto-creation is disabled in tenant config
    auto_create_enabled = tenant.get("auto_create_media_buys", True)

    if manual_approval_required and "create_media_buy" in manual_approval_operations:
        # Handle manual approval case - simplified for brevity
        return CreateMediaBuyResponse(
            media_buy_id=f"pending_{time.time()}",
            status="pending_manual",
            detail="Manual approval required",
            creative_deadline=None,
            message="Your media buy request requires manual approval.",
            context_id=None,
        )

    # Check if tenant disables auto-creation
    if not auto_create_enabled:
        return CreateMediaBuyResponse(
            media_buy_id=f"pending_{time.time()}",
            status="pending_manual",
            detail="Tenant configuration disables auto-creation",
            creative_deadline=None,
            message="This media buy requires manual approval due to tenant configuration.",
            context_id=None,
        )

    # Get products for the media buy
    catalog = get_product_catalog()
    products_in_buy = [p for p in catalog if p.product_id in req.product_ids]

    # Convert products to MediaPackages
    packages = []
    for product in products_in_buy:
        format_info = product.formats[0] if product.formats else None
        packages.append(
            MediaPackage(
                package_id=product.product_id,
                name=product.name,
                delivery_type=product.delivery_type,
                cpm=product.cpm if product.cpm else 10.0,
                impressions=int(req.total_budget / (product.cpm if product.cpm else 10.0) * 1000),
                format_ids=[format_info.format_id] if format_info else [],
            )
        )

    # Create the media buy using the adapter
    start_time_dt = datetime.combine(req.flight_start_date, datetime.min.time())
    end_time_dt = datetime.combine(req.flight_end_date, datetime.max.time())
    response = adapter.create_media_buy(req, packages, start_time_dt, end_time_dt)

    # Store the media buy in memory
    media_buys[response.media_buy_id] = (req, principal_id)

    # Store the media buy in database
    with get_db_session() as session:
        new_media_buy = MediaBuy(
            media_buy_id=response.media_buy_id,
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            order_name=req.po_number or f"Order-{response.media_buy_id}",
            advertiser_name=principal.name,
            campaign_objective=getattr(req, "campaign_objective", ""),
            kpi_goal=getattr(req, "kpi_goal", ""),
            budget=req.total_budget,
            start_date=req.flight_start_date.isoformat(),
            end_date=req.flight_end_date.isoformat(),
            status=response.status or "active",
            raw_request=req.model_dump(mode="json"),
            context_id=None,
        )
        session.add(new_media_buy)
        session.commit()

    # Handle creatives if provided
    if req.creatives:
        assets = []
        for creative in req.creatives:
            assets.append({
                "id": creative.creative_id,
                "name": f"Creative {creative.creative_id}",
                "format": "image",
                "media_url": creative.content_uri,
                "click_url": "https://example.com",
                "package_assignments": req.product_ids,
            })
        statuses = adapter.add_creative_assets(response.media_buy_id, assets, datetime.now())
        for status in statuses:
            creative_statuses[status.creative_id] = CreativeStatus(
                creative_id=status.creative_id,
                status="approved" if status.status == "approved" else "pending_review",
                detail="Creative submitted to ad server",
            )

    # Add message to response
    response.message = f"Media buy {response.media_buy_id} has been created successfully. Your campaign will run from {req.flight_start_date} to {req.flight_end_date} with a budget of ${req.total_budget}."

    # Log activity
    log_tool_activity(context, "create_media_buy", start_time)

    return response


# Import functions that are referenced but not yet defined
def get_product_catalog():
    """Get the product catalog - will be imported from product_tools."""
    from src.core.product_tools import get_product_catalog
    return get_product_catalog()
