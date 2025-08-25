"""Core schema models for the AdCP system."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


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
    description: str
    assets: list[Asset] = Field(default_factory=list, description="List of assets required for this format")
    delivery_options: DeliveryOptions


class DaypartSchedule(BaseModel):
    """Time-based targeting schedule."""

    days: list[int] = Field(..., description="Days of week (0=Sunday, 6=Saturday)")
    start_hour: int = Field(..., ge=0, le=23, description="Start hour (0-23)")
    end_hour: int = Field(..., ge=0, le=23, description="End hour (0-23)")
    timezone: str | None = Field("UTC", description="Timezone for schedule")


class Dayparting(BaseModel):
    """Dayparting configuration for time-based targeting."""

    timezone: str = Field("UTC", description="Default timezone for all schedules")
    schedules: list[DaypartSchedule] = Field(..., description="List of time windows")
    # Special presets for audio
    presets: list[str] | None = Field(None, description="Named presets like 'drive_time_morning'")


class FrequencyCap(BaseModel):
    """Simple frequency capping configuration.

    Provides basic impression suppression at the media buy or package level.
    More sophisticated frequency management is handled by the AEE layer.
    """

    suppress_minutes: int = Field(..., gt=0, description="Suppress impressions for this many minutes after serving")
    scope: Literal["media_buy", "package"] = Field("media_buy", description="Apply at media buy or package level")


class Principal(BaseModel):
    """Principal (advertiser) information."""

    principal_id: str = Field(..., description="Unique identifier for the principal")
    name: str = Field(..., description="Human-readable name for the principal")
    platform_mappings: dict[str, Any] = Field(default_factory=dict, description="Platform-specific mappings")


class PriceGuidance(BaseModel):
    """Price guidance for products."""

    p10: float | None = Field(None, description="10th percentile price")
    p50: float | None = Field(None, description="50th percentile (median) price")
    p90: float | None = Field(None, description="90th percentile price")
    currency: str = Field("USD", description="Currency for pricing")

