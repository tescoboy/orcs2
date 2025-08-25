"""Targeting schema models for the AdCP system."""

from typing import Any, Literal, Union

from pydantic import BaseModel, Field


class TargetingCapability(BaseModel):
    """Defines targeting dimension capabilities and restrictions."""

    dimension: str  # e.g., "geo_country", "key_value"
    access: Literal["overlay", "managed_only", "both"] = "overlay"
    description: str | None = None
    allowed_values: list[str] | None = None  # For restricted value sets
    aee_signal: bool | None = False  # Whether this is an AEE signal dimension


class Targeting(BaseModel):
    """Comprehensive targeting options for media buys.

    All fields are optional and can be combined for precise audience targeting.
    Platform adapters will map these to their specific targeting capabilities.
    Uses any_of/none_of pattern for consistent include/exclude across all dimensions.
    """

    # Geographic targeting
    geo_country_any_of: list[str] | None = Field(None, description="Include countries (ISO codes)")
    geo_country_none_of: list[str] | None = Field(None, description="Exclude countries (ISO codes)")
    geo_state_any_of: list[str] | None = Field(None, description="Include states/provinces")
    geo_state_none_of: list[str] | None = Field(None, description="Exclude states/provinces")
    geo_city_any_of: list[str] | None = Field(None, description="Include cities")
    geo_city_none_of: list[str] | None = Field(None, description="Exclude cities")
    geo_dma_any_of: list[str] | None = Field(None, description="Include DMAs")
    geo_dma_none_of: list[str] | None = Field(None, description="Exclude DMAs")
    geo_zip_any_of: list[str] | None = Field(None, description="Include ZIP codes")
    geo_zip_none_of: list[str] | None = Field(None, description="Exclude ZIP codes")

    # Demographic targeting
    demo_age_any_of: list[str] | None = Field(None, description="Include age groups (e.g., ['18-24', '25-34'])")
    demo_age_none_of: list[str] | None = Field(None, description="Exclude age groups")
    demo_gender_any_of: list[str] | None = Field(None, description="Include genders (e.g., ['male', 'female'])")
    demo_gender_none_of: list[str] | None = Field(None, description="Exclude genders")
    demo_income_any_of: list[str] | None = Field(None, description="Include income brackets")
    demo_income_none_of: list[str] | None = Field(None, description="Exclude income brackets")
    demo_education_any_of: list[str] | None = Field(None, description="Include education levels")
    demo_education_none_of: list[str] | None = Field(None, description="Exclude education levels")

    # Interest and behavioral targeting
    interests_any_of: list[str] | None = Field(None, description="Include interest categories")
    interests_none_of: list[str] | None = Field(None, description="Exclude interest categories")
    behaviors_any_of: list[str] | None = Field(None, description="Include behavioral segments")
    behaviors_none_of: list[str] | None = Field(None, description="Exclude behavioral segments")

    # Contextual targeting
    content_category_any_of: list[str] | None = Field(None, description="Include content categories")
    content_category_none_of: list[str] | None = Field(None, description="Exclude content categories")
    content_keywords_any_of: list[str] | None = Field(None, description="Include content keywords")
    content_keywords_none_of: list[str] | None = Field(None, description="Exclude content keywords")

    # Device and technical targeting
    device_type_any_of: list[str] | None = Field(None, description="Include device types (e.g., ['mobile', 'desktop'])")
    device_type_none_of: list[str] | None = Field(None, description="Exclude device types")
    browser_any_of: list[str] | None = Field(None, description="Include browsers")
    browser_none_of: list[str] | None = Field(None, description="Exclude browsers")
    os_any_of: list[str] | None = Field(None, description="Include operating systems")
    os_none_of: list[str] | None = Field(None, description="Exclude operating systems")

    # Custom targeting
    key_value_any_of: dict[str, list[str]] | None = Field(None, description="Include key-value pairs")
    key_value_none_of: dict[str, list[str]] | None = Field(None, description="Exclude key-value pairs")

    # Advanced targeting
    audience_segments_any_of: list[str] | None = Field(None, description="Include audience segments")
    audience_segments_none_of: list[str] | None = Field(None, description="Exclude audience segments")
    lookalike_audiences_any_of: list[str] | None = Field(None, description="Include lookalike audiences")
    lookalike_audiences_none_of: list[str] | None = Field(None, description="Exclude lookalike audiences")

    # Time-based targeting
    dayparting: Union["Dayparting", None] = Field(None, description="Time-based targeting schedule")

    # Frequency capping
    frequency_cap: Union["FrequencyCap", None] = Field(None, description="Frequency capping configuration")

    # Additional targeting options
    additional_targeting: dict[str, Any] | None = Field(None, description="Platform-specific targeting options")


class TargetingDimensionInfo(BaseModel):
    """Information about a specific targeting dimension."""

    dimension: str = Field(..., description="Dimension name (e.g., 'geo_country')")
    display_name: str = Field(..., description="Human-readable name")
    description: str | None = Field(None, description="Detailed description")
    data_type: Literal["string", "number", "boolean", "list"] = Field(..., description="Data type for values")
    allowed_values: list[str] | None = Field(None, description="Restricted set of allowed values")
    is_required: bool = Field(False, description="Whether this dimension is required")
    is_aee_signal: bool = Field(False, description="Whether this is an AEE signal dimension")


class ChannelTargetingCapabilities(BaseModel):
    """Targeting capabilities for a specific channel."""

    channel: str = Field(..., description="Channel identifier")
    dimensions: list[TargetingDimensionInfo] = Field(..., description="Available targeting dimensions")
    supports_dayparting: bool = Field(False, description="Whether dayparting is supported")
    supports_frequency_capping: bool = Field(False, description="Whether frequency capping is supported")
    max_targeting_dimensions: int | None = Field(None, description="Maximum number of targeting dimensions")
    additional_capabilities: dict[str, Any] | None = Field(None, description="Channel-specific capabilities")
