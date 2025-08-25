"""
Media buy request/response Pydantic models.
Extracted from schemas.py to reduce file size and improve maintainability.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


# --- Media Buy Request/Response Models ---
class CreateMediaBuyRequest(BaseModel):
    total_budget: float
    targeting_overlay: dict[str, Any] | None = None
    dry_run: bool = False


class CreateMediaBuyResponse(BaseModel):
    media_buy_id: str
    context_id: str
    status: str
    message: str | None = None


class CheckMediaBuyStatusRequest(BaseModel):
    context_id: str


class CheckMediaBuyStatusResponse(BaseModel):
    media_buy_id: str
    context_id: str
    status: str
    total_budget: float | None = None
    targeting_overlay: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UpdateMediaBuyRequest(BaseModel):
    media_buy_id: str
    total_budget: float | None = None
    targeting_overlay: dict[str, Any] | None = None
    status: str | None = None
    dry_run: bool = False


class UpdateMediaBuyResponse(BaseModel):
    media_buy_id: str
    status: str
    message: str | None = None


class GetMediaBuyDeliveryRequest(BaseModel):
    media_buy_id: str


class GetMediaBuyDeliveryResponse(BaseModel):
    media_buy_id: str
    delivery_data: dict[str, Any]


class GetAllMediaBuyDeliveryRequest(BaseModel):
    pass


class GetAllMediaBuyDeliveryResponse(BaseModel):
    principal_id: str
    delivery_data: list[dict[str, Any]]


# --- Creative Asset Models ---
class CreativeAsset(BaseModel):
    name: str
    type: str
    url: str | None = None
    size: int | None = None
    format: str | None = None


class AddCreativeAssetsRequest(BaseModel):
    media_buy_id: str
    creative_assets: list[CreativeAsset]
    dry_run: bool = False


class AddCreativeAssetsResponse(BaseModel):
    media_buy_id: str
    creative_assets: list[dict[str, Any]]
    status: str
    message: str | None = None


class CheckCreativeStatusRequest(BaseModel):
    media_buy_id: str
    creative_asset_ids: list[str]


class CheckCreativeStatusResponse(BaseModel):
    media_buy_id: str
    creative_asset_ids: list[str]
    status_data: dict[str, Any]


class ApproveAdaptationRequest(BaseModel):
    media_buy_id: str
    adaptation_id: str
    approval_notes: str | None = None
    dry_run: bool = False


class ApproveAdaptationResponse(BaseModel):
    media_buy_id: str
    adaptation_id: str
    new_creative_id: str
    status: str
    message: str | None = None


class GetCreativesRequest(BaseModel):
    media_buy_id: str


class GetCreativesResponse(BaseModel):
    media_buy_id: str
    creatives: list[dict[str, Any]]


class CreateCreativeGroupRequest(BaseModel):
    name: str
    description: str | None = None
    creative_ids: list[str]
    dry_run: bool = False


class CreateCreativeGroupResponse(BaseModel):
    group_id: str
    name: str
    status: str
    message: str | None = None


class CreateCreativeRequest(BaseModel):
    name: str
    description: str | None = None
    format: str
    size: str | None = None
    content: dict[str, Any] | None = None
    dry_run: bool = False


class CreateCreativeResponse(BaseModel):
    creative_id: str
    name: str
    status: str
    message: str | None = None


class AssignCreativeRequest(BaseModel):
    media_buy_id: str
    creative_id: str
    assignment_type: str
    dry_run: bool = False


class AssignCreativeResponse(BaseModel):
    media_buy_id: str
    creative_id: str
    status: str
    message: str | None = None


# --- Legacy Models ---
class LegacyUpdateMediaBuyRequest(BaseModel):
    media_buy_id: str
    new_total_budget: float | None = None
    new_targeting_overlay: dict[str, Any] | None = None
    creative_assignments: list[dict[str, Any]] | None = None


class UpdatePackageRequest(BaseModel):
    media_buy_id: str
    total_budget: float | None = None
    targeting_overlay: dict[str, Any] | None = None
    dry_run: bool = False


# --- Admin Models ---
class GetPendingCreativesRequest(BaseModel):
    limit: int | None = None


class GetPendingCreativesResponse(BaseModel):
    creatives: list[dict[str, Any]]


class ApproveCreativeRequest(BaseModel):
    creative_id: str
    approval_notes: str | None = None


class ApproveCreativeResponse(BaseModel):
    creative_id: str
    status: str
    message: str | None = None


class UpdatePerformanceIndexRequest(BaseModel):
    creative_id: str
    performance_index: float


class UpdatePerformanceIndexResponse(BaseModel):
    creative_id: str
    performance_index: float
    status: str
    message: str | None = None


# --- Product Models ---
class GetProductsRequest(BaseModel):
    tenant_id: str | None = None
    limit: int | None = None
    offset: int | None = None


class GetProductsResponse(BaseModel):
    products: list[dict[str, Any]]
    total_count: int
    has_more: bool
