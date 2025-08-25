"""
Task and workflow Pydantic models.
Extracted from schemas.py to reduce file size and improve maintainability.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HumanTask(BaseModel):
    task_id: str
    context_id: str
    step_id: str
    task_type: str
    title: str
    description: str | None = None
    assigned_to: str
    priority: str = "medium"
    due_by: datetime | None = None
    status: str = "pending"
    completed_by: str | None = None
    completed_at: datetime | None = None
    completion_notes: str | None = None
    verified_by: str | None = None
    verified_at: datetime | None = None
    verification_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CreateHumanTaskRequest(BaseModel):
    task_type: str
    title: str
    description: str | None = None
    assigned_to: str = "principal"
    priority: str = "medium"
    due_in_hours: int | None = None


class CreateHumanTaskResponse(BaseModel):
    task_id: str
    status: str
    due_by: datetime | None = None


class GetPendingTasksRequest(BaseModel):
    owner_filter: str | None = None
    task_type: str | None = None
    principal_id: str | None = None
    limit: int | None = None


class GetPendingTasksResponse(BaseModel):
    tasks: list[dict[str, Any]]


class AssignTaskRequest(BaseModel):
    task_id: str
    assigned_to: str


class CompleteTaskRequest(BaseModel):
    task_id: str
    completion_notes: str | None = None


class VerifyTaskRequest(BaseModel):
    task_id: str
    verification_notes: str | None = None


class VerifyTaskResponse(BaseModel):
    task_id: str
    status: str
    verified_by: str
    verified_at: datetime
    message: str | None = None


class MarkTaskCompleteRequest(BaseModel):
    task_id: str
    completed_by: str
    completion_notes: str | None = None
    verification_notes: str | None = None
