"""
Pydantic models for the application.
This file has been refactored to import from smaller, focused modules.
Original schemas.py was 969 lines - now split into logical modules.
"""

# Import all models from the split modules
from .schemas_core import (
    Asset,
    DeliveryOptions,
    Format,
    DaypartSchedule,
    Dayparting,
    FrequencyCap,
    PriceGuidance,
    Product,
    Principal,
    ProductPerformance,
)

from .schemas_targeting import (
    TargetingCapability,
    Targeting,
)

from .schemas_creative import (
    CreativeGroup,
    Creative,
    CreativeAdaptation,
    CreativeStatus,
)

from .schemas_media_buy import (
    CreateMediaBuyRequest,
    CreateMediaBuyResponse,
    CheckMediaBuyStatusRequest,
    CheckMediaBuyStatusResponse,
    UpdateMediaBuyRequest,
    UpdateMediaBuyResponse,
    GetMediaBuyDeliveryRequest,
    GetMediaBuyDeliveryResponse,
    GetAllMediaBuyDeliveryRequest,
    GetAllMediaBuyDeliveryResponse,
    CreativeAsset,
    AddCreativeAssetsRequest,
    AddCreativeAssetsResponse,
    CheckCreativeStatusRequest,
    CheckCreativeStatusResponse,
    ApproveAdaptationRequest,
    ApproveAdaptationResponse,
    GetCreativesRequest,
    GetCreativesResponse,
    CreateCreativeGroupRequest,
    CreateCreativeGroupResponse,
    CreateCreativeRequest,
    CreateCreativeResponse,
    AssignCreativeRequest,
    AssignCreativeResponse,
    LegacyUpdateMediaBuyRequest,
    UpdatePackageRequest,
    GetPendingCreativesRequest,
    GetPendingCreativesResponse,
    ApproveCreativeRequest,
    ApproveCreativeResponse,
    UpdatePerformanceIndexRequest,
    UpdatePerformanceIndexResponse,
    GetProductsRequest,
    GetProductsResponse,
)

from .schemas_tasks import (
    HumanTask,
    CreateHumanTaskRequest,
    CreateHumanTaskResponse,
    GetPendingTasksRequest,
    GetPendingTasksResponse,
    AssignTaskRequest,
    CompleteTaskRequest,
    VerifyTaskRequest,
    VerifyTaskResponse,
    MarkTaskCompleteRequest,
)

from .schemas_signals import (
    GetTargetingCapabilitiesRequest,
    TargetingDimensionInfo,
    ChannelTargetingCapabilities,
    GetTargetingCapabilitiesResponse,
    CheckAEERequirementsRequest,
    CheckAEERequirementsResponse,
    Signal,
    GetSignalsRequest,
    GetSignalsResponse,
)

# Export all models for backward compatibility
__all__ = [
    # Core models
    "Asset",
    "DeliveryOptions", 
    "Format",
    "DaypartSchedule",
    "Dayparting",
    "FrequencyCap",
    "PriceGuidance",
    "Product",
    "Principal",
    "ProductPerformance",
    
    # Targeting models
    "TargetingCapability",
    "Targeting",
    
    # Creative models
    "CreativeGroup",
    "Creative",
    "CreativeAdaptation", 
    "CreativeStatus",
    
    # Media buy models
    "CreateMediaBuyRequest",
    "CreateMediaBuyResponse",
    "CheckMediaBuyStatusRequest",
    "CheckMediaBuyStatusResponse",
    "UpdateMediaBuyRequest",
    "UpdateMediaBuyResponse",
    "GetMediaBuyDeliveryRequest",
    "GetMediaBuyDeliveryResponse",
    "GetAllMediaBuyDeliveryRequest",
    "GetAllMediaBuyDeliveryResponse",
    "CreativeAsset",
    "AddCreativeAssetsRequest",
    "AddCreativeAssetsResponse",
    "CheckCreativeStatusRequest",
    "CheckCreativeStatusResponse",
    "ApproveAdaptationRequest",
    "ApproveAdaptationResponse",
    "GetCreativesRequest",
    "GetCreativesResponse",
    "CreateCreativeGroupRequest",
    "CreateCreativeGroupResponse",
    "CreateCreativeRequest",
    "CreateCreativeResponse",
    "AssignCreativeRequest",
    "AssignCreativeResponse",
    "LegacyUpdateMediaBuyRequest",
    "UpdatePackageRequest",
    "GetPendingCreativesRequest",
    "GetPendingCreativesResponse",
    "ApproveCreativeRequest",
    "ApproveCreativeResponse",
    "UpdatePerformanceIndexRequest",
    "UpdatePerformanceIndexResponse",
    "GetProductsRequest",
    "GetProductsResponse",
    
    # Task models
    "HumanTask",
    "CreateHumanTaskRequest",
    "CreateHumanTaskResponse",
    "GetPendingTasksRequest",
    "GetPendingTasksResponse",
    "AssignTaskRequest",
    "CompleteTaskRequest",
    "VerifyTaskRequest",
    "VerifyTaskResponse",
    "MarkTaskCompleteRequest",
    
    # Signal models
    "GetTargetingCapabilitiesRequest",
    "TargetingDimensionInfo",
    "ChannelTargetingCapabilities",
    "GetTargetingCapabilitiesResponse",
    "CheckAEERequirementsRequest",
    "CheckAEERequirementsResponse",
    "Signal",
    "GetSignalsRequest",
    "GetSignalsResponse",
]
