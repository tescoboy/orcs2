"""Media buy model classes for the AdCP system."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .core import FrequencyCap
from .creative_models import Creative
from .targeting import Targeting


class MediaPackage(BaseModel):
    """Package within a media buy."""

    package_id: str = Field(..., description="Package identifier")
    name: str = Field(..., description="Package name")
    delivery_type: str = Field(..., description="Delivery type")
    cpm: float = Field(..., description="Cost per thousand impressions")
    impressions: int = Field(..., description="Number of impressions")
    format_ids: list[str] = Field(..., description="Format identifiers")


class ReportingPeriod(BaseModel):
    """Reporting period for delivery data."""

    start_date: date = Field(..., description="Period start date")
    end_date: date = Field(..., description="Period end date")
    granularity: str = Field(..., description="Data granularity")


class DeliveryTotals(BaseModel):
    """Total delivery metrics."""

    impressions: int = Field(0, description="Total impressions")
    clicks: int = Field(0, description="Total clicks")
    conversions: int = Field(0, description="Total conversions")
    spend: float = Field(0.0, description="Total spend")


class PackagePerformance(BaseModel):
    """Performance metrics for a package."""

    package_id: str = Field(..., description="Package identifier")
    metrics: DeliveryTotals = Field(..., description="Performance metrics")


class AssetStatus(BaseModel):
    """Status of a creative asset."""

    creative_id: str = Field(..., description="Creative identifier")
    status: str = Field(..., description="Asset status")
    detail: str | None = Field(None, description="Status details")


class PackageUpdate(BaseModel):
    """Update for a package."""

    package_id: str = Field(..., description="Package identifier")
    updates: dict[str, Any] = Field(..., description="Updates to apply")


class MediaBuyDeliveryData(BaseModel):
    """Delivery data for a media buy."""

    delivery_date: date = Field(..., description="Date of the delivery data")
    impressions: int = Field(0, description="Number of impressions")
    clicks: int = Field(0, description="Number of clicks")
    conversions: int = Field(0, description="Number of conversions")
    spend: float = Field(0.0, description="Amount spent")
    ctr: float = Field(0.0, description="Click-through rate")
    cpc: float = Field(0.0, description="Cost per click")
    cpm: float = Field(0.0, description="Cost per thousand impressions")
    breakdowns: dict[str, Any] | None = Field(None, description="Breakdown data by dimension")


class PackageDelivery(BaseModel):
    """Delivery data for a package."""

    package_id: str = Field(..., description="Package identifier")
    delivery_data: list[MediaBuyDeliveryData] = Field(..., description="Delivery data for the package")
