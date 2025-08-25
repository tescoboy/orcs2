"""Product catalog and targeting related functions."""

import logging
from typing import Any

from src.core.config_loader import get_current_tenant
from src.core.database.database_session import get_db_session
from src.core.database.models import Product as ModelProduct
from src.core.schemas import Product
from product_catalog_providers.factory import get_product_catalog_provider

logger = logging.getLogger(__name__)


def get_product_catalog() -> list[Product]:
    """Get the product catalog for the current tenant."""
    tenant = get_current_tenant()
    
    # Get products from database
    with get_db_session() as session:
        products = session.query(ModelProduct).filter_by(tenant_id=tenant["tenant_id"]).all()
        
        # Convert to schema objects
        catalog = []
        for product in products:
            catalog.append(Product(
                product_id=product.product_id,
                name=product.name,
                description=product.description,
                formats=product.formats or [],
                targeting_template=product.targeting_template or {},
                cpm=product.cpm,
                delivery_type=product.delivery_type,
                countries=product.countries or [],
                implementation_config=product.implementation_config or {}
            ))
    
    return catalog


def get_targeting_capabilities():
    """Get targeting capabilities for the current tenant."""
    tenant = get_current_tenant()
    
    # Import targeting capabilities
    from src.services.targeting_dimensions import get_targeting_dimensions
    
    dimensions = get_targeting_dimensions()
    
    return {
        "dimensions": dimensions,
        "tenant_id": tenant["tenant_id"],
        "enable_aee_signals": tenant.get("enable_aee_signals", False)
    }


def check_aee_requirements(req, context):
    """Check AEE (Audience Extension Engine) requirements."""
    tenant = get_current_tenant()
    
    if not tenant.get("enable_aee_signals", False):
        return {
            "aee_enabled": False,
            "message": "AEE signals are not enabled for this tenant"
        }
    
    # Check if the request meets AEE requirements
    # This is a simplified implementation
    aee_requirements = {
        "minimum_budget": 1000,
        "minimum_duration_days": 7,
        "required_targeting": ["geo", "demo"]
    }
    
    # Validate requirements
    violations = []
    
    if req.total_budget < aee_requirements["minimum_budget"]:
        violations.append(f"Budget must be at least ${aee_requirements['minimum_budget']}")
    
    duration_days = (req.flight_end_date - req.flight_start_date).days
    if duration_days < aee_requirements["minimum_duration_days"]:
        violations.append(f"Campaign must run for at least {aee_requirements['minimum_duration_days']} days")
    
    if req.targeting_overlay:
        targeting_keys = list(req.targeting_overlay.keys())
        for required in aee_requirements["required_targeting"]:
            if required not in targeting_keys:
                violations.append(f"Targeting must include {required}")
    
    return {
        "aee_enabled": True,
        "requirements_met": len(violations) == 0,
        "violations": violations,
        "message": "AEE requirements met" if len(violations) == 0 else f"AEE requirements not met: {'; '.join(violations)}"
    }

