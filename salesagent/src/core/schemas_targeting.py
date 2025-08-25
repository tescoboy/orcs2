"""
Targeting-related Pydantic models.
Extracted from schemas.py to reduce file size and improve maintainability.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class TargetingCapability(BaseModel):
    dimension: str
    display_name: str
    description: str | None = None
    type: Literal["string", "number", "boolean", "list", "range"]
    required: bool = False
    options: list[str] | None = None  # For string/list types
    min_value: float | None = None  # For number/range types
    max_value: float | None = None  # For number/range types
    unit: str | None = None  # e.g., "USD", "miles", "years"


class Targeting(BaseModel):
    # Geographic targeting
    countries: list[str] | None = None
    states: list[str] | None = None
    cities: list[str] | None = None
    zip_codes: list[str] | None = None
    radius_miles: int | None = None  # For location-based targeting

    # Demographic targeting
    age_min: int | None = None
    age_max: int | None = None
    genders: list[str] | None = None
    income_min: float | None = None
    income_max: float | None = None
    education_levels: list[str] | None = None
    marital_status: list[str] | None = None

    # Behavioral targeting
    interests: list[str] | None = None
    behaviors: list[str] | None = None
    purchase_intent: list[str] | None = None
    life_events: list[str] | None = None

    # Device/Technology targeting
    device_types: list[str] | None = None  # mobile, desktop, tablet, tv
    operating_systems: list[str] | None = None
    browsers: list[str] | None = None
    connection_types: list[str] | None = None  # wifi, cellular, broadband

    # Content/Context targeting
    content_categories: list[str] | None = None
    content_keywords: list[str] | None = None
    site_categories: list[str] | None = None
    site_domains: list[str] | None = None

    # Time-based targeting
    dayparting: dict[str, Any] | None = None  # Dayparting configuration
    frequency_caps: list[dict[str, Any]] | None = None  # Frequency cap rules

    # Custom/Audience targeting
    custom_audiences: list[str] | None = None
    lookalike_audiences: list[str] | None = None
    retargeting_lists: list[str] | None = None

    # Platform-specific custom targeting
    custom: dict[str, Any] | None = None  # Platform-specific targeting options

    # Key-value targeting (managed-only for AEE signals)
    # These are not exposed in overlay - only set by orchestrator/AEE
    key_value_pairs: dict[str, str] | None = None  # e.g., {"aee_segment": "high_value", "aee_score": "0.85"}
