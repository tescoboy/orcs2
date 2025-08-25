"""
Product catalog and targeting operations.
Extracted from main.py to reduce file size and improve maintainability.
"""

import logging
from typing import Any, Dict, List

from fastmcp import FastMCP
from fastmcp.server.context import Context

from src.core.config_loader import get_current_tenant
from src.core.database.database_session import get_db_session
from src.core.database.models import Product as ModelProduct
from src.core.schemas import (
    CheckAEERequirementsRequest,
    CheckAEERequirementsResponse,
)
from src.core.utils import get_principal_from_context, get_principal_object
from product_catalog_providers.factory import get_product_catalog_provider

logger = logging.getLogger(__name__)


def get_product_catalog() -> list[Dict[str, Any]]:
    """Get products for the current tenant."""
    tenant = get_current_tenant()

    with get_db_session() as session:
        products = session.query(ModelProduct).filter_by(tenant_id=tenant["tenant_id"]).all()

        loaded_products = []
        for product in products:
            # Convert ORM model to Pydantic schema
            product_data = {
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "tenant_id": product.tenant_id,
                "cpm": product.cpm,
                "formats": product.formats,
                "targeting_template": product.targeting_template,
                "delivery_type": product.delivery_type,
                "is_fixed_price": product.is_fixed_price,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
            }
            loaded_products.append(product_data)

    return loaded_products


def get_targeting_capabilities(
    principal_id: str,
    adapter_type: str = None,
    include_advanced: bool = True,
) -> Dict[str, Any]:
    """Get targeting capabilities for a principal."""
    principal = get_principal_object(principal_id)
    if not principal:
        raise ValueError(f"Principal {principal_id} not found")

    # Get product catalog provider
    provider = get_product_catalog_provider("database")
    
    try:
        # Get targeting capabilities from provider
        capabilities = provider.get_targeting_capabilities(
            principal_id=principal_id,
            adapter_type=adapter_type,
            include_advanced=include_advanced,
        )
        
        return capabilities
    except Exception as e:
        logger.error(f"Error getting targeting capabilities: {e}")
        # Return basic capabilities as fallback
        return {
            "basic_targeting": {
                "geographic": ["country", "state", "city"],
                "demographic": ["age", "gender", "income"],
                "behavioral": ["interests", "affinities"],
            },
            "advanced_targeting": {
                "custom_audiences": [],
                "lookalike_audiences": [],
                "retargeting": [],
            } if include_advanced else {},
            "supported_formats": ["display", "video", "native"],
            "supported_sizes": ["300x250", "728x90", "160x600"],
        }


@FastMCP.tool
def check_aee_requirements(req: CheckAEERequirementsRequest, context: Context) -> CheckAEERequirementsResponse:
    """Check AEE (Automated Environment Evaluation) requirements for a media buy."""
    principal_id = get_principal_from_context(context)
    if not principal_id:
        raise ValueError("No principal ID found in context")

    tenant = get_current_tenant()

    try:
        # Get product catalog provider
        provider = get_product_catalog_provider("database")
        
        # Check AEE requirements
        requirements = provider.check_aee_requirements(
            principal_id=principal_id,
            media_buy_id=req.media_buy_id,
            targeting_overlay=req.targeting_overlay,
            creative_assets=req.creative_assets,
        )
        
        return CheckAEERequirementsResponse(
            media_buy_id=req.media_buy_id,
            requirements_met=requirements.get("requirements_met", False),
            missing_requirements=requirements.get("missing_requirements", []),
            recommendations=requirements.get("recommendations", []),
            compliance_score=requirements.get("compliance_score", 0.0),
        )

    except Exception as e:
        logger.error(f"Error checking AEE requirements: {e}")
        raise
