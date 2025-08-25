"""
SQLAlchemy models for database schema.
This file has been refactored to import from smaller, focused modules.
Original models.py was 708 lines - now split into logical modules.
"""

# Import all models from the split modules to ensure SQLAlchemy can find them
from .models_core import (
    Base,
    Tenant,
    CreativeFormat,
    Product,
    Principal,
    User,
)

from .models_media import (
    MediaBuy,
    Task,
    HumanTask,
    AuditLog,
)

from .models_workflow import (
    SuperadminConfig,
    AdapterConfig,
    SyncJob,
    Context,
    WorkflowStep,
    ObjectWorkflowMapping,
)

from .models_gam import (
    GAMInventory,
    ProductInventoryMapping,
    GAMOrder,
    GAMLineItem,
)

from .models_buyer import (
    BuyerCampaign,
    BuyerCampaignProduct,
)

# Ensure all models are imported for SQLAlchemy metadata
__all__ = [
    # Core models
    "Base",
    "Tenant",
    "CreativeFormat",
    "Product",
    "Principal",
    "User",
    
    # Media models
    "MediaBuy",
    "Task",
    "HumanTask",
    "AuditLog",
    
    # Workflow models
    "SuperadminConfig",
    "AdapterConfig",
    "SyncJob",
    "Context",
    "WorkflowStep",
    "ObjectWorkflowMapping",
    
    # GAM models
    "GAMInventory",
    "ProductInventoryMapping",
    "GAMOrder",
    "GAMLineItem",
    
    # Buyer models
    "BuyerCampaign",
    "BuyerCampaignProduct",
]
