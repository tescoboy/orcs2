"""Main schemas module - imports from all modular schema files."""

# Import from core schemas
from .core import (
    DeliveryOptions, Asset, Format, DaypartSchedule, Dayparting, 
    FrequencyCap, Principal, PriceGuidance,
)

# Import from targeting schemas
from .targeting import (
    TargetingCapability, Targeting, TargetingDimensionInfo, ChannelTargetingCapabilities,
)

# Import from product schemas
from .product import (
    Product, ProductPerformance, UpdatePerformanceIndexRequest, 
    UpdatePerformanceIndexResponse, GetProductsRequest, GetProductsResponse,
)

# Import from creative schemas
from .creative_models import (
    CreativeGroup, Creative, CreativeAdaptation, CreativeStatus, CreativeAssignment,
)
from .creative import (
    AddCreativeAssetsRequest, AddCreativeAssetsResponse, CheckCreativeStatusRequest,
    CheckCreativeStatusResponse, CreateCreativeGroupRequest, CreateCreativeGroupResponse,
    CreateCreativeRequest, CreateCreativeResponse, AssignCreativeRequest, AssignCreativeResponse,
    GetCreativesRequest, GetCreativesResponse, GetPendingCreativesRequest,
    GetPendingCreativesResponse, ApproveCreativeRequest, ApproveCreativeResponse, AdaptCreativeRequest,
)

# Import from media buy schemas
from .media_buy_models import (
    MediaPackage, ReportingPeriod, DeliveryTotals, PackagePerformance,
    AssetStatus, PackageUpdate, PackageDelivery, MediaBuyDeliveryData,
)
from .media_buy import (
    CreateMediaBuyRequest, CreateMediaBuyResponse, CheckMediaBuyStatusRequest,
    CheckMediaBuyStatusResponse, LegacyUpdateMediaBuyRequest, GetMediaBuyDeliveryRequest,
    GetMediaBuyDeliveryResponse, GetAllMediaBuyDeliveryRequest,
    GetAllMediaBuyDeliveryResponse, UpdateMediaBuyResponse, UpdatePackageRequest,
    UpdateMediaBuyRequest, AdapterGetMediaBuyDeliveryResponse,
)

# Import from human tasks schemas
from .human_tasks_models import HumanTask
from .human_tasks import (
    CreateHumanTaskRequest, CreateHumanTaskResponse, GetPendingTasksRequest,
    GetPendingTasksResponse, AssignTaskRequest, CompleteTaskRequest, VerifyTaskRequest,
    VerifyTaskResponse, MarkTaskCompleteRequest, GetTargetingCapabilitiesRequest,
    GetTargetingCapabilitiesResponse, CheckAEERequirementsRequest, CheckAEERequirementsResponse,
)

# Import from signals schemas
from .signals import (
    Signal, GetSignalsRequest, GetSignalsResponse,
)

# Export all classes for backward compatibility
__all__ = [
    # Core
    "DeliveryOptions", "Asset", "Format", "DaypartSchedule", "Dayparting", 
    "FrequencyCap", "Principal", "PriceGuidance",
    
    # Targeting
    "TargetingCapability", "Targeting", "TargetingDimensionInfo", "ChannelTargetingCapabilities",
    
    # Product
    "Product", "ProductPerformance", "UpdatePerformanceIndexRequest", 
    "UpdatePerformanceIndexResponse", "GetProductsRequest", "GetProductsResponse",
    
    # Creative
    "CreativeGroup", "Creative", "CreativeAdaptation", "CreativeStatus", "CreativeAssignment",
    "AddCreativeAssetsRequest", "AddCreativeAssetsResponse", "CheckCreativeStatusRequest",
    "CheckCreativeStatusResponse", "CreateCreativeGroupRequest", "CreateCreativeGroupResponse",
    "CreateCreativeRequest", "CreateCreativeResponse", "AssignCreativeRequest", "AssignCreativeResponse",
    "GetCreativesRequest", "GetCreativesResponse", "GetPendingCreativesRequest",
    "GetPendingCreativesResponse", "ApproveCreativeRequest", "ApproveCreativeResponse", "AdaptCreativeRequest",
    
    # Media Buy
    "MediaPackage", "ReportingPeriod", "DeliveryTotals", "PackagePerformance",
    "AssetStatus", "PackageUpdate", "PackageDelivery", "MediaBuyDeliveryData",
    "CreateMediaBuyRequest", "CreateMediaBuyResponse", "CheckMediaBuyStatusRequest",
    "CheckMediaBuyStatusResponse", "LegacyUpdateMediaBuyRequest", "GetMediaBuyDeliveryRequest",
    "GetMediaBuyDeliveryResponse", "GetAllMediaBuyDeliveryRequest",
    "GetAllMediaBuyDeliveryResponse", "UpdateMediaBuyResponse", "UpdatePackageRequest",
    "UpdateMediaBuyRequest", "AdapterGetMediaBuyDeliveryResponse",
    
    # Human Tasks
    "HumanTask", "CreateHumanTaskRequest", "CreateHumanTaskResponse", "GetPendingTasksRequest",
    "GetPendingTasksResponse", "AssignTaskRequest", "CompleteTaskRequest", "VerifyTaskRequest",
    "VerifyTaskResponse", "MarkTaskCompleteRequest", "GetTargetingCapabilitiesRequest",
    "GetTargetingCapabilitiesResponse", "CheckAEERequirementsRequest", "CheckAEERequirementsResponse",
    
    # Signals
    "Signal", "GetSignalsRequest", "GetSignalsResponse",
]
