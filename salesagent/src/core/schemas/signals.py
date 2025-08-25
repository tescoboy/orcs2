"""Signal schema models for the AdCP system."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Signal(BaseModel):
    """AEE (Audience Extension Engine) signal information."""

    signal_id: str = Field(..., description="Unique identifier for the signal")
    signal_type: str = Field(..., description="Type of signal")
    name: str = Field(..., description="Human-readable signal name")
    description: str | None = Field(None, description="Detailed signal description")
    
    # Signal properties
    category: str = Field(..., description="Signal category")
    subcategory: str | None = Field(None, description="Signal subcategory")
    audience_size: int | None = Field(None, description="Estimated audience size")
    coverage_percentage: float | None = Field(None, description="Coverage percentage")
    
    # Targeting information
    targeting_dimensions: list[str] = Field(default_factory=list, description="Targeting dimensions this signal affects")
    targeting_values: dict[str, Any] | None = Field(None, description="Targeting values for this signal")
    
    # Performance metrics
    performance_score: float | None = Field(None, description="Performance score (0-1)")
    conversion_rate: float | None = Field(None, description="Historical conversion rate")
    ctr: float | None = Field(None, description="Historical click-through rate")
    
    # Availability and pricing
    is_available: bool = Field(True, description="Whether the signal is currently available")
    price_multiplier: float | None = Field(None, description="Price multiplier for this signal")
    minimum_budget: float | None = Field(None, description="Minimum budget required")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="When the signal was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the signal was last updated")
    expires_at: datetime | None = Field(None, description="When the signal expires")
    
    # Additional properties
    metadata: dict[str, Any] | None = Field(None, description="Additional signal metadata")


class GetSignalsRequest(BaseModel):
    """Request to get available signals."""

    signal_type: str | None = Field(None, description="Filter by signal type")
    category: str | None = Field(None, description="Filter by category")
    targeting_dimension: str | None = Field(None, description="Filter by targeting dimension")
    min_audience_size: int | None = Field(None, description="Minimum audience size")
    min_performance_score: float | None = Field(None, description="Minimum performance score")
    available_only: bool = Field(True, description="Whether to return only available signals")
    limit: int = Field(50, description="Maximum number of signals to return")
    offset: int = Field(0, description="Number of signals to skip")


class GetSignalsResponse(BaseModel):
    """Response containing available signals."""

    signals: list[Signal] = Field(..., description="List of available signals")
    total_count: int = Field(0, description="Total number of signals available")
    has_more: bool = Field(False, description="Whether there are more signals available")
    categories: list[str] = Field(default_factory=list, description="Available signal categories")
    targeting_dimensions: list[str] = Field(default_factory=list, description="Available targeting dimensions")

