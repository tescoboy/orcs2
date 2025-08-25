"""Creative request/response schema models for the AdCP system."""

from typing import Any

from pydantic import BaseModel, Field

from .creative_models import Creative, CreativeStatus


class AddCreativeAssetsRequest(BaseModel):
    """Request to add creative assets to a media buy."""

    media_buy_id: str = Field(..., description="Media buy identifier")
    creatives: list[Creative] = Field(..., description="Creative assets to add")


class AddCreativeAssetsResponse(BaseModel):
    """Response to adding creative assets."""

    success: bool = Field(..., description="Whether the operation was successful")
    added_count: int = Field(0, description="Number of creatives added")
    statuses: list[CreativeStatus] = Field(default_factory=list, description="Status of each creative")
    message: str | None = Field(None, description="Response message")


class CheckCreativeStatusRequest(BaseModel):
    """Request to check creative status."""

    creative_ids: list[str] = Field(..., description="Creative identifiers to check")


class CheckCreativeStatusResponse(BaseModel):
    """Response to creative status check."""

    statuses: list[CreativeStatus] = Field(..., description="Status of each creative")


class CreateCreativeGroupRequest(BaseModel):
    """Request to create a creative group."""

    name: str = Field(..., description="Group name")
    description: str | None = Field(None, description="Group description")
    format_id: str = Field(..., description="Format ID")


class CreateCreativeGroupResponse(BaseModel):
    """Response to creating a creative group."""

    group_id: str = Field(..., description="Created group identifier")
    success: bool = Field(True, description="Whether the operation was successful")


class CreateCreativeRequest(BaseModel):
    """Request to create a creative."""

    name: str = Field(..., description="Creative name")
    description: str | None = Field(None, description="Creative description")
    format_id: str = Field(..., description="Format ID")
    content_uri: str = Field(..., description="Content URI")
    content_type: str = Field(..., description="Content type")
    group_id: str | None = Field(None, description="Creative group ID")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class CreateCreativeResponse(BaseModel):
    """Response to creating a creative."""

    creative_id: str = Field(..., description="Created creative identifier")
    success: bool = Field(True, description="Whether the operation was successful")


class AssignCreativeRequest(BaseModel):
    """Request to assign a creative to a media buy."""

    media_buy_id: str = Field(..., description="Media buy identifier")
    creative_id: str = Field(..., description="Creative identifier")
    package_id: str | None = Field(None, description="Package identifier")
    priority: int = Field(1, description="Priority for creative rotation")
    weight: float = Field(1.0, description="Weight for creative rotation")
    start_date: str | None = Field(None, description="Assignment start date")
    end_date: str | None = Field(None, description="Assignment end date")


class AssignCreativeResponse(BaseModel):
    """Response to assigning a creative."""

    assignment_id: str = Field(..., description="Assignment identifier")
    success: bool = Field(True, description="Whether the operation was successful")


class GetCreativesRequest(BaseModel):
    """Request to get creatives."""

    media_buy_id: str | None = Field(None, description="Filter by media buy ID")
    group_id: str | None = Field(None, description="Filter by creative group ID")
    status: str | None = Field(None, description="Filter by status")
    limit: int = Field(50, description="Maximum number of creatives to return")
    offset: int = Field(0, description="Number of creatives to skip")


class GetCreativesResponse(BaseModel):
    """Response containing creatives."""

    creatives: list[Creative] = Field(..., description="List of creatives")
    total_count: int = Field(0, description="Total number of creatives available")


class GetPendingCreativesRequest(BaseModel):
    """Request to get pending creatives for review."""

    reviewer_id: str | None = Field(None, description="Reviewer identifier")
    limit: int = Field(50, description="Maximum number of creatives to return")
    offset: int = Field(0, description="Number of creatives to skip")


class GetPendingCreativesResponse(BaseModel):
    """Response containing pending creatives."""

    creatives: list[Creative] = Field(..., description="List of pending creatives")
    total_count: int = Field(0, description="Total number of pending creatives")


class ApproveCreativeRequest(BaseModel):
    """Request to approve a creative."""

    creative_id: str = Field(..., description="Creative identifier")
    reviewer_id: str = Field(..., description="Reviewer identifier")
    notes: str | None = Field(None, description="Approval notes")


class ApproveCreativeResponse(BaseModel):
    """Response to approving a creative."""

    success: bool = Field(..., description="Whether the approval was successful")
    message: str | None = Field(None, description="Response message")


class AdaptCreativeRequest(BaseModel):
    """Request to adapt a creative."""

    creative_id: str = Field(..., description="Original creative identifier")
    adaptation_type: str = Field(..., description="Type of adaptation to perform")
    adaptation_parameters: dict[str, Any] = Field(..., description="Parameters for the adaptation")
