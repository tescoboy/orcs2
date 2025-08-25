"""Creative model classes for the AdCP system."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CreativeGroup(BaseModel):
    """Group of related creatives."""

    group_id: str = Field(..., description="Unique identifier for the creative group")
    name: str = Field(..., description="Human-readable name for the group")
    description: str | None = Field(None, description="Description of the creative group")
    format_id: str = Field(..., description="Format this group is designed for")
    status: Literal["draft", "pending", "approved", "rejected"] = Field("draft", description="Group status")


class Creative(BaseModel):
    """Creative asset information."""

    creative_id: str = Field(..., description="Unique identifier for the creative")
    name: str = Field(..., description="Human-readable name for the creative")
    description: str | None = Field(None, description="Description of the creative")
    format_id: str = Field(..., description="Format this creative is designed for")
    content_uri: str = Field(..., description="URI to the creative content")
    content_type: str = Field(..., description="MIME type of the creative content")
    dimensions: dict[str, int] | None = Field(None, description="Width and height of the creative")
    duration: int | None = Field(None, description="Duration in seconds (for video/audio)")
    file_size: int | None = Field(None, description="File size in bytes")
    status: Literal["draft", "pending", "approved", "rejected"] = Field("draft", description="Creative status")
    metadata: dict[str, Any] | None = Field(None, description="Additional creative metadata")


class CreativeAdaptation(BaseModel):
    """Creative adaptation information."""

    adaptation_id: str = Field(..., description="Unique identifier for the adaptation")
    original_creative_id: str = Field(..., description="ID of the original creative")
    adapted_creative: Creative = Field(..., description="The adapted creative")
    adaptation_type: str = Field(..., description="Type of adaptation performed")
    adaptation_reason: str | None = Field(None, description="Reason for the adaptation")
    status: Literal["pending", "approved", "rejected"] = Field("pending", description="Adaptation status")


class CreativeStatus(BaseModel):
    """Status information for a creative."""

    creative_id: str = Field(..., description="Creative identifier")
    status: Literal["pending", "approved", "rejected"] = Field(..., description="Current status")
    detail: str | None = Field(None, description="Status details or rejection reason")
    reviewed_by: str | None = Field(None, description="User who reviewed the creative")
    reviewed_at: datetime | None = Field(None, description="When the creative was reviewed")


class CreativeAssignment(BaseModel):
    """Assignment of creatives to media buys."""

    assignment_id: str = Field(..., description="Unique identifier for the assignment")
    media_buy_id: str = Field(..., description="Media buy identifier")
    creative_id: str = Field(..., description="Creative identifier")
    package_id: str | None = Field(None, description="Package identifier (if applicable)")
    priority: int = Field(1, description="Priority of this creative in the rotation")
    weight: float = Field(1.0, description="Weight for creative rotation")
    start_date: datetime | None = Field(None, description="When this assignment becomes active")
    end_date: datetime | None = Field(None, description="When this assignment expires")
    status: Literal["active", "paused", "ended"] = Field("active", description="Assignment status")

