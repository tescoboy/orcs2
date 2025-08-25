"""Human-in-the-loop task model classes for the AdCP system."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class HumanTask(BaseModel):
    """Human-in-the-loop task information."""

    task_id: str = Field(..., description="Unique identifier for the task")
    task_type: Literal["manual_approval", "creative_review", "policy_review", "quality_check"] = Field(..., description="Type of task")
    priority: Literal["low", "medium", "high", "urgent"] = Field("medium", description="Task priority")
    status: Literal["pending", "assigned", "in_progress", "completed", "cancelled"] = Field("pending", description="Task status")
    
    # Associated entities
    media_buy_id: str | None = Field(None, description="Associated media buy ID")
    creative_id: str | None = Field(None, description="Associated creative ID")
    operation: str = Field(..., description="Operation that triggered this task")
    
    # Task details
    title: str = Field(..., description="Human-readable task title")
    description: str = Field(..., description="Detailed task description")
    error_detail: str | None = Field(None, description="Error details if task was created due to an error")
    
    # Context and data
    context_data: dict[str, Any] = Field(default_factory=dict, description="Context data for the task")
    request_data: dict[str, Any] | None = Field(None, description="Original request data")
    
    # Assignment and timing
    assigned_to: str | None = Field(None, description="User assigned to the task")
    assigned_at: datetime | None = Field(None, description="When the task was assigned")
    due_at: datetime | None = Field(None, description="When the task is due")
    completed_at: datetime | None = Field(None, description="When the task was completed")
    
    # Results
    result: dict[str, Any] | None = Field(None, description="Task result data")
    notes: str | None = Field(None, description="Notes from the task completion")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="When the task was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the task was last updated")

