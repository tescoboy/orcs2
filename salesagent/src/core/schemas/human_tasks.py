"""Human-in-the-loop task request/response schema models for the AdCP system."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from .human_tasks_models import HumanTask


class CreateHumanTaskRequest(BaseModel):
    """Request to create a human task."""

    task_type: Literal["manual_approval", "creative_review", "policy_review", "quality_check"] = Field(..., description="Type of task")
    priority: Literal["low", "medium", "high", "urgent"] = Field("medium", description="Task priority")
    media_buy_id: str | None = Field(None, description="Associated media buy ID")
    operation: str = Field(..., description="Operation that triggered this task")
    error_detail: str | None = Field(None, description="Error details if applicable")
    context_data: dict[str, Any] = Field(default_factory=dict, description="Context data for the task")
    due_in_hours: int = Field(24, description="Hours until task is due")


class CreateHumanTaskResponse(BaseModel):
    """Response to creating a human task."""

    task_id: str = Field(..., description="Created task identifier")
    success: bool = Field(True, description="Whether the operation was successful")
    message: str | None = Field(None, description="Response message")


class GetPendingTasksRequest(BaseModel):
    """Request to get pending tasks."""

    task_type: str | None = Field(None, description="Filter by task type")
    priority: str | None = Field(None, description="Filter by priority")
    assigned_to: str | None = Field(None, description="Filter by assigned user")
    limit: int = Field(50, description="Maximum number of tasks to return")
    offset: int = Field(0, description="Number of tasks to skip")


class GetPendingTasksResponse(BaseModel):
    """Response containing pending tasks."""

    tasks: list[HumanTask] = Field(..., description="List of pending tasks")
    total_count: int = Field(0, description="Total number of pending tasks")
    has_more: bool = Field(False, description="Whether there are more tasks available")


class AssignTaskRequest(BaseModel):
    """Request to assign a task to a user."""

    task_id: str = Field(..., description="Task identifier")
    assigned_to: str = Field(..., description="User to assign the task to")
    notes: str | None = Field(None, description="Assignment notes")


class CompleteTaskRequest(BaseModel):
    """Request to complete a task."""

    task_id: str = Field(..., description="Task identifier")
    result: dict[str, Any] = Field(..., description="Task result data")
    notes: str | None = Field(None, description="Completion notes")
    approved: bool = Field(..., description="Whether the task was approved")


class VerifyTaskRequest(BaseModel):
    """Request to verify a task completion."""

    task_id: str = Field(..., description="Task identifier")
    verification_data: dict[str, Any] = Field(..., description="Verification data")
    verified_by: str = Field(..., description="User performing the verification")
    notes: str | None = Field(None, description="Verification notes")


class VerifyTaskResponse(BaseModel):
    """Response to task verification."""

    task_id: str = Field(..., description="Task identifier")
    verification_status: Literal["verified", "rejected", "needs_revision"] = Field(..., description="Verification status")
    message: str | None = Field(None, description="Verification message")
    next_actions: list[str] | None = Field(None, description="Next actions required")


class MarkTaskCompleteRequest(BaseModel):
    """Request to mark a task as complete."""

    task_id: str = Field(..., description="Task identifier")
    completed_by: str = Field(..., description="User completing the task")
    result: dict[str, Any] = Field(..., description="Task result")
    notes: str | None = Field(None, description="Completion notes")
    auto_approve: bool = Field(False, description="Whether to auto-approve the task")


class GetTargetingCapabilitiesRequest(BaseModel):
    """Request to get targeting capabilities."""

    channel: str | None = Field(None, description="Filter by channel")
    include_aee_signals: bool = Field(True, description="Whether to include AEE signal dimensions")


class GetTargetingCapabilitiesResponse(BaseModel):
    """Response containing targeting capabilities."""

    channels: list["ChannelTargetingCapabilities"] = Field(..., description="Targeting capabilities by channel")
    global_dimensions: list["TargetingDimensionInfo"] = Field(..., description="Global targeting dimensions")


class CheckAEERequirementsRequest(BaseModel):
    """Request to check AEE requirements."""

    targeting_overlay: dict[str, Any] | None = Field(None, description="Targeting overlay to check")
    budget: float | None = Field(None, description="Campaign budget")
    duration_days: int | None = Field(None, description="Campaign duration in days")


class CheckAEERequirementsResponse(BaseModel):
    """Response to AEE requirements check."""

    aee_enabled: bool = Field(..., description="Whether AEE is enabled")
    requirements_met: bool = Field(..., description="Whether requirements are met")
    violations: list[str] = Field(default_factory=list, description="List of requirement violations")
    message: str = Field(..., description="Human-readable message")
    recommended_actions: list[str] = Field(default_factory=list, description="Recommended actions to meet requirements")
