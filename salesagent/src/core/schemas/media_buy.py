"""Media buy request/response schema models for the AdCP system."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .core import FrequencyCap
from .creative_models import Creative
from .targeting import Targeting
from .media_buy_models import (
    MediaPackage, ReportingPeriod, DeliveryTotals, PackagePerformance,
    AssetStatus, PackageUpdate, PackageDelivery, MediaBuyDeliveryData
)


class CreateMediaBuyRequest(BaseModel):
    """Request to create a new media buy."""

    # Basic information
    po_number: str | None = Field(None, description="Purchase order number")
    campaign_objective: str | None = Field(None, description="Campaign objective")
    kpi_goal: str | None = Field(None, description="KPI goal for the campaign")
    
    # Product selection
    product_ids: list[str] = Field(..., description="List of product IDs to include in the media buy")
    
    # Budget and timing
    total_budget: float = Field(..., gt=0, description="Total budget for the media buy")
    flight_start_date: date = Field(..., description="Campaign start date")
    flight_end_date: date = Field(..., description="Campaign end date")
    
    # Targeting
    targeting_overlay: Targeting | None = Field(None, description="Additional targeting overlay")
    
    # Creatives
    creatives: list[Creative] | None = Field(None, description="Creative assets to include")
    
    # Frequency capping
    frequency_cap: FrequencyCap | None = Field(None, description="Frequency capping configuration")
    
    # Additional options
    additional_options: dict[str, Any] | None = Field(None, description="Platform-specific options")


class CreateMediaBuyResponse(BaseModel):
    """Response to creating a media buy."""

    media_buy_id: str = Field(..., description="Unique identifier for the created media buy")
    status: str = Field(..., description="Status of the media buy")
    detail: str | None = Field(None, description="Additional details about the status")
    creative_deadline: datetime | None = Field(None, description="Deadline for creative submission")
    message: str | None = Field(None, description="Human-readable message")
    context_id: str | None = Field(None, description="Context ID for async operations")


class CheckMediaBuyStatusRequest(BaseModel):
    """Request to check media buy status."""

    media_buy_id: str = Field(..., description="Media buy identifier")


class CheckMediaBuyStatusResponse(BaseModel):
    """Response to media buy status check."""

    media_buy_id: str = Field(..., description="Media buy identifier")
    status: str = Field(..., description="Current status")
    detail: str | None = Field(None, description="Status details")
    progress: float | None = Field(None, description="Progress percentage (0-100)")
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")


class LegacyUpdateMediaBuyRequest(BaseModel):
    """Legacy request to update a media buy."""

    media_buy_id: str = Field(..., description="Media buy identifier")
    updates: dict[str, Any] = Field(..., description="Updates to apply")


class GetMediaBuyDeliveryRequest(BaseModel):
    """Request to get delivery data for a media buy."""

    media_buy_id: str = Field(..., description="Media buy identifier")
    start_date: date | None = Field(None, description="Start date for delivery data")
    end_date: date | None = Field(None, description="End date for delivery data")
    granularity: Literal["hourly", "daily", "weekly", "monthly"] = Field("daily", description="Data granularity")
    include_breakdowns: bool = Field(False, description="Whether to include breakdown data")


class GetMediaBuyDeliveryResponse(BaseModel):
    """Response to media buy delivery request."""

    media_buy_id: str = Field(..., description="Media buy identifier")
    delivery_data: list[MediaBuyDeliveryData] = Field(..., description="Delivery data")
    summary: dict[str, Any] = Field(..., description="Summary statistics")
    last_updated: datetime = Field(..., description="When the data was last updated")


class GetAllMediaBuyDeliveryRequest(BaseModel):
    """Request to get delivery data for all media buys."""

    principal_id: str | None = Field(None, description="Filter by principal ID")
    start_date: date | None = Field(None, description="Start date for delivery data")
    end_date: date | None = Field(None, description="End date for delivery data")
    status: str | None = Field(None, description="Filter by status")


class GetAllMediaBuyDeliveryResponse(BaseModel):
    """Response to all media buy delivery request."""

    media_buys: list[GetMediaBuyDeliveryResponse] = Field(..., description="Delivery data for all media buys")
    total_count: int = Field(0, description="Total number of media buys")


class UpdateMediaBuyResponse(BaseModel):
    """Response to updating a media buy."""

    media_buy_id: str = Field(..., description="Media buy identifier")
    success: bool = Field(..., description="Whether the update was successful")
    message: str | None = Field(None, description="Response message")


class UpdatePackageRequest(BaseModel):
    """Request to update packages in a media buy."""

    media_buy_id: str = Field(..., description="Media buy identifier")
    package_updates: list[PackageUpdate] = Field(..., description="Package updates")


class UpdateMediaBuyRequest(BaseModel):
    """Request to update a media buy."""

    media_buy_id: str = Field(..., description="Media buy identifier")
    total_budget: float | None = Field(None, description="New total budget")
    flight_start_date: date | None = Field(None, description="New start date")
    flight_end_date: date | None = Field(None, description="New end date")
    status: str | None = Field(None, description="New status")
    targeting_overlay: Targeting | None = Field(None, description="New targeting overlay")
    frequency_cap: FrequencyCap | None = Field(None, description="New frequency cap")
    additional_options: dict[str, Any] | None = Field(None, description="New additional options")


class AdapterGetMediaBuyDeliveryResponse(BaseModel):
    """Adapter response for media buy delivery."""

    media_buy_id: str = Field(..., description="Media buy identifier")
    packages: list[PackageDelivery] = Field(..., description="Delivery data by package")
    summary: DeliveryTotals = Field(..., description="Overall summary")
    last_updated: datetime = Field(..., description="When the data was last updated")
