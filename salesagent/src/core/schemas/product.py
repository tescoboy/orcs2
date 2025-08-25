"""Product schema models for the AdCP system."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from .core import PriceGuidance


class Product(BaseModel):
    """Product information for advertising inventory."""

    product_id: str = Field(..., description="Unique identifier for the product")
    name: str = Field(..., description="Human-readable name for the product")
    description: str | None = Field(None, description="Detailed description of the product")
    type: Literal["video", "audio", "display", "native", "dooh"] = Field(..., description="Product type")
    delivery_type: Literal["guaranteed", "non_guaranteed"] = Field(..., description="Delivery type")
    
    # Pricing information
    cpm: float | None = Field(None, description="Cost per thousand impressions")
    price_guidance: PriceGuidance | None = Field(None, description="Price guidance for the product")
    
    # Format and creative information
    formats: list[dict[str, Any]] = Field(default_factory=list, description="Supported creative formats")
    targeting_template: dict[str, Any] | None = Field(None, description="Default targeting template")
    
    # Geographic and availability information
    countries: list[str] | None = Field(None, description="Available countries (ISO codes)")
    availability: dict[str, Any] | None = Field(None, description="Availability information")
    
    # Implementation details
    implementation_config: dict[str, Any] | None = Field(None, description="Platform-specific implementation details")
    
    # Additional metadata
    metadata: dict[str, Any] | None = Field(None, description="Additional product metadata")


class ProductPerformance(BaseModel):
    """Performance metrics for a product."""

    product_id: str = Field(..., description="Product identifier")
    impressions: int = Field(0, description="Total impressions")
    clicks: int = Field(0, description="Total clicks")
    conversions: int = Field(0, description="Total conversions")
    spend: float = Field(0.0, description="Total spend")
    ctr: float = Field(0.0, description="Click-through rate")
    cpc: float = Field(0.0, description="Cost per click")
    cpm: float = Field(0.0, description="Cost per thousand impressions")
    conversion_rate: float = Field(0.0, description="Conversion rate")
    cpa: float = Field(0.0, description="Cost per acquisition")


class UpdatePerformanceIndexRequest(BaseModel):
    """Request to update performance index for products."""

    products: list[ProductPerformance] = Field(..., description="Performance data for products")


class UpdatePerformanceIndexResponse(BaseModel):
    """Response to performance index update request."""

    success: bool = Field(..., description="Whether the update was successful")
    updated_count: int = Field(0, description="Number of products updated")
    message: str | None = Field(None, description="Response message")


class GetProductsRequest(BaseModel):
    """Request to get products."""

    filters: dict[str, Any] | None = Field(None, description="Filter criteria")
    limit: int = Field(50, description="Maximum number of products to return")
    offset: int = Field(0, description="Number of products to skip")


class GetProductsResponse(BaseModel):
    """Response containing products."""

    products: list[Product] = Field(..., description="List of products")
    total_count: int = Field(0, description="Total number of products available")
    has_more: bool = Field(False, description="Whether there are more products available")

