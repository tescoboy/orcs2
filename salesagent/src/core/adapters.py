"""
Adapter management and initialization functions.
Extracted from main.py to reduce file size and improve maintainability.
"""

import logging
from typing import Any

from src.adapters.google_ad_manager import GoogleAdManager
from src.adapters.kevel import Kevel
from src.adapters.mock_ad_server import MockAdServer as MockAdServerAdapter
from src.adapters.mock_creative_engine import MockCreativeEngine
from src.adapters.triton_digital import TritonDigital
from src.core.schemas import Principal
from src.core.utils import get_adapter_principal_id

logger = logging.getLogger(__name__)


def get_adapter(principal: Principal, dry_run: bool = False):
    """
    Get the appropriate adapter based on principal configuration.
    
    Args:
        principal: Principal object containing adapter configuration
        dry_run: Whether to use mock adapters for testing
        
    Returns:
        Configured adapter instance
    """
    if dry_run:
        return MockAdServerAdapter()
    
    # Check which adapters are configured for this principal
    platform_mappings = principal.platform_mappings or {}
    
    # Priority order: Google Ad Manager, Kevel, Triton Digital, Mock
    if "google_ad_manager" in platform_mappings:
        gam_config = platform_mappings["google_ad_manager"]
        gam_principal_id = get_adapter_principal_id(principal.principal_id, "google_ad_manager")
        
        if gam_principal_id:
            return GoogleAdManager(
                principal_id=gam_principal_id,
                network_code=gam_config.get("network_code"),
                client_id=gam_config.get("client_id"),
                client_secret=gam_config.get("client_secret"),
                refresh_token=gam_config.get("refresh_token"),
                developer_token=gam_config.get("developer_token"),
                login_customer_id=gam_config.get("login_customer_id"),
                manager_customer_id=gam_config.get("manager_customer_id"),
            )
    
    if "kevel" in platform_mappings:
        kevel_config = platform_mappings["kevel"]
        kevel_principal_id = get_adapter_principal_id(principal.principal_id, "kevel")
        
        if kevel_principal_id:
            return Kevel(
                principal_id=kevel_principal_id,
                api_key=kevel_config.get("api_key"),
                network_id=kevel_config.get("network_id"),
                base_url=kevel_config.get("base_url"),
            )
    
    if "triton_digital" in platform_mappings:
        triton_config = platform_mappings["triton_digital"]
        triton_principal_id = get_adapter_principal_id(principal.principal_id, "triton_digital")
        
        if triton_principal_id:
            return TritonDigital(
                principal_id=triton_principal_id,
                api_key=triton_config.get("api_key"),
                network_id=triton_config.get("network_id"),
                base_url=triton_config.get("base_url"),
            )
    
    # Fallback to mock adapter
    logger.warning(f"No valid adapter configuration found for principal {principal.principal_id}, using mock adapter")
    return MockAdServerAdapter()


def get_creative_engine(principal: Principal, dry_run: bool = False):
    """
    Get the creative engine adapter.
    
    Args:
        principal: Principal object
        dry_run: Whether to use mock adapters for testing
        
    Returns:
        Configured creative engine instance
    """
    if dry_run:
        return MockCreativeEngine()
    
    # For now, always use mock creative engine
    # TODO: Implement real creative engine adapters
    return MockCreativeEngine()
