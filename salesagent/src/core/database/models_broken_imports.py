"""
SQLAlchemy models for database schema - Fixed version.
This file ensures all models are imported in the correct order to resolve relationship issues.
"""

# Import all models in the correct order to ensure SQLAlchemy can resolve relationships
from .models_core import Base
from .models_media import MediaBuy, Task, HumanTask, AuditLog
from .models_workflow import SuperadminConfig, AdapterConfig, SyncJob, Context, WorkflowStep, ObjectWorkflowMapping
from .models_gam import GAMInventory, ProductInventoryMapping, GAMOrder, GAMLineItem
from .models_buyer import BuyerCampaign, BuyerCampaignProduct
from .models_core import Tenant, CreativeFormat, Product, Principal, User

# Export all models
__all__ = [
    "Base",
    "Tenant",
    "CreativeFormat", 
    "Product",
    "Principal",
    "User",
    "MediaBuy",
    "Task",
    "HumanTask",
    "AuditLog",
    "SuperadminConfig",
    "AdapterConfig",
    "SyncJob",
    "Context",
    "WorkflowStep",
    "ObjectWorkflowMapping",
    "GAMInventory",
    "ProductInventoryMapping",
    "GAMOrder",
    "GAMLineItem",
    "BuyerCampaign",
    "BuyerCampaignProduct",
]
