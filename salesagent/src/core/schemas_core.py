"""
Core Pydantic models for the application.
Extracted from schemas.py to reduce file size and improve maintainability.
"""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# --- Core Models ---
class DeliveryOptions(BaseModel):
    hosted: dict[str, Any] | None = None
    vast: dict[str, Any] | None = None


class Asset(BaseModel):
    """Individual asset within a creative format."""

    asset_id: str = Field(..., description="Unique identifier for this asset within the format")
    asset_type: Literal["video", "image", "text", "url", "audio", "html"] = Field(..., description="Type of asset")
    required: bool = Field(True, description="Whether this asset is required")

    # Common properties
    name: str | None = Field(None, description="Human-readable name for the asset")
    description: str | None = Field(None, description="Description of the asset's purpose")

    # Type-specific properties (flattened structure)
    # Video properties
    duration_seconds: int | None = Field(None, description="Video duration in seconds")
    min_bitrate_mbps: float | None = Field(None, description="Minimum bitrate in Mbps")
    max_bitrate_mbps: float | None = Field(None, description="Maximum bitrate in Mbps")

    # Image/Display properties
    width: int | None = Field(None, description="Width in pixels")
    height: int | None = Field(None, description="Height in pixels")

    # File properties
    acceptable_formats: list[str] | None = Field(None, description="Acceptable file formats (e.g., ['mp4', 'webm'])")
    max_file_size_mb: float | None = Field(None, description="Maximum file size in MB")

    # Text properties
    max_length: int | None = Field(None, description="Maximum character length for text")

    # Additional specifications
    additional_specs: dict[str, Any] | None = Field(None, description="Any additional asset-specific requirements")


class Format(BaseModel):
    format_id: str
    name: str
    type: Literal["video", "audio", "display", "native", "dooh"]
    description: str | None = None
    assets: list[Asset]
    delivery_options: DeliveryOptions | None = None
    additional_specs: dict[str, Any] | None = None


class DaypartSchedule(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format


class Dayparting(BaseModel):
    enabled: bool = False
    schedules: list[DaypartSchedule] | None = None


class FrequencyCap(BaseModel):
    max_impressions: int | None = None
    max_clicks: int | None = None
    time_window_hours: int = 24
    scope: Literal["user", "household", "device"] = "user"


class PriceGuidance(BaseModel):
    floor: float
    p25: float | None = None
    p50: float | None = None
    p75: float | None = None
    p90: float | None = None


class Product(BaseModel):
    product_id: str
    name: str
    description: str
    formats: list[Format]
    tenant_id: str
    cpm: float
    targeting_template: dict[str, Any] | None = None
    delivery_type: str = "standard"
    is_fixed_price: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Principal(BaseModel):
    principal_id: str
    tenant_id: str
    access_token: str
    platform_mappings: dict[str, Any]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProductPerformance(BaseModel):
    product_id: str
    performance_index: float
    last_updated: datetime
