"""
Task operations (under 150 lines).
Extracted from task_management.py to maintain the 150-line limit.
"""

import logging
from datetime import datetime
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.context import Context

from src.core.audit_logger import get_audit_logger
from src.core.config_loader import get_current_tenant
from src.core.database.database_session import get_db_session
from src.core.database.models import HumanTask as ModelHumanTask
from src.core.schemas import (
    AssignTaskRequest,
    CompleteTaskRequest,
    VerifyTaskRequest,
    VerifyTaskResponse,
    MarkTaskCompleteRequest,
)
from src.core.utils import get_principal_from_context
from src.services.activity_feed import activity_feed

logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()


def _get_principal_id_from_context(context: Context) -> str:
    """Get principal ID from context."""
    principal_id = get_principal_from_context(context)
    if not principal_id:
        raise ValueError("No principal ID found in context")
    return principal_id


def _require_admin(context: Context) -> None:
    """Require admin privileges for the current user."""
    principal_id = get_principal_from_context(context)
    tenant = get_current_tenant()
    is_admin = principal_id == f"{tenant['tenant_id']}_admin"
    
    if not is_admin:
        raise ValueError("Admin privileges required")


@FastMCP.tool
def assign_task(req: AssignTaskRequest, context: Context) -> dict[str, str]:
    """Assign a task to a specific user or role."""
    _require_admin(context)
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    try:
        with get_db_session() as session:
            task = session.query(ModelHumanTask).filter_by(task_id=req.task_id).first()
            if not task:
                raise ValueError(f"Task {req.task_id} not found")

            task.assigned_to = req.assigned_to
            task.updated_at = datetime.utcnow()
            session.commit()

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="assign_task",
            details={
                "task_id": req.task_id,
                "assigned_to": req.assigned_to,
            },
        )

        return {"status": "success", "message": f"Task assigned to {req.assigned_to}"}

    except Exception as e:
        logger.error(f"Error assigning task: {e}")
        raise


@FastMCP.tool
def complete_task(req: CompleteTaskRequest, context: Context) -> dict[str, str]:
    """Mark a task as completed."""
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    try:
        with get_db_session() as session:
            task = session.query(ModelHumanTask).filter_by(task_id=req.task_id).first()
            if not task:
                raise ValueError(f"Task {req.task_id} not found")

            # Check if user has permission to complete this task
            if task.assigned_to != "principal" and task.assigned_to != principal_id:
                is_admin = principal_id == f"{tenant['tenant_id']}_admin"
                if not is_admin:
                    raise ValueError(f"User {principal_id} does not have permission to complete task {req.task_id}")

            task.status = "completed"
            task.completed_by = principal_id
            task.completed_at = datetime.utcnow()
            task.completion_notes = req.completion_notes
            task.updated_at = datetime.utcnow()
            session.commit()

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="complete_task",
            details={
                "task_id": req.task_id,
                "completion_notes": req.completion_notes,
            },
        )

        return {"status": "success", "message": "Task completed successfully"}

    except Exception as e:
        logger.error(f"Error completing task: {e}")
        raise


@FastMCP.tool
def verify_task(req: VerifyTaskRequest, context: Context) -> VerifyTaskResponse:
    """Verify a completed task."""
    _require_admin(context)
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    try:
        with get_db_session() as session:
            task = session.query(ModelHumanTask).filter_by(task_id=req.task_id).first()
            if not task:
                raise ValueError(f"Task {req.task_id} not found")

            if task.status != "completed":
                raise ValueError(f"Task {req.task_id} is not completed")

            task.status = "verified"
            task.verified_by = principal_id
            task.verified_at = datetime.utcnow()
            task.verification_notes = req.verification_notes
            task.updated_at = datetime.utcnow()
            session.commit()

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="verify_task",
            details={
                "task_id": req.task_id,
                "verification_notes": req.verification_notes,
            },
        )

        return VerifyTaskResponse(
            task_id=req.task_id,
            status="verified",
            verified_by=principal_id,
            verified_at=datetime.utcnow(),
            message="Task verified successfully",
        )

    except Exception as e:
        logger.error(f"Error verifying task: {e}")
        raise


@FastMCP.tool
def mark_task_complete(req: MarkTaskCompleteRequest, context: Context) -> dict[str, Any]:
    """Mark a task as complete with verification."""
    _require_admin(context)
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    try:
        with get_db_session() as session:
            task = session.query(ModelHumanTask).filter_by(task_id=req.task_id).first()
            if not task:
                raise ValueError(f"Task {req.task_id} not found")

            # Mark as completed
            task.status = "completed"
            task.completed_by = req.completed_by
            task.completed_at = datetime.utcnow()
            task.completion_notes = req.completion_notes

            # If verification is provided, mark as verified
            if req.verification_notes:
                task.status = "verified"
                task.verified_by = principal_id
                task.verified_at = datetime.utcnow()
                task.verification_notes = req.verification_notes

            task.updated_at = datetime.utcnow()
            session.commit()

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="mark_task_complete",
            details={
                "task_id": req.task_id,
                "completed_by": req.completed_by,
                "verification_notes": req.verification_notes,
            },
        )

        return {
            "task_id": req.task_id,
            "status": task.status,
            "completed_by": req.completed_by,
            "verified_by": principal_id if req.verification_notes else None,
            "message": f"Task marked complete by {req.completed_by}",
        }

    except Exception as e:
        logger.error(f"Error marking task complete: {e}")
        raise
