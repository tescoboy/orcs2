"""
Task management and workflow operations.
Extracted from main.py to reduce file size and improve maintainability.
"""

import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastmcp import FastMCP
from fastmcp.server.context import Context

from src.core.audit_logger import get_audit_logger
from src.core.config_loader import get_current_tenant
from src.core.context_manager import get_context_manager
from src.core.database.database_session import get_db_session
from src.core.database.models import Task, HumanTask as ModelHumanTask
from src.core.schemas import (
    CreateHumanTaskRequest,
    CreateHumanTaskResponse,
    GetPendingTasksRequest,
    GetPendingTasksResponse,
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


def log_tool_activity(context: Context, tool_name: str, start_time: float = None):
    """Log tool activity for audit purposes."""
    if start_time is None:
        start_time = time.time()
    
    duration = time.time() - start_time
    principal_id = get_principal_from_context(context)
    tenant = get_current_tenant()
    
    audit_logger.log_activity(
        tenant_id=tenant["tenant_id"],
        principal_id=principal_id,
        action=tool_name,
        duration=duration,
        status="success"
    )


@FastMCP.tool
def create_workflow_step_for_task(req: CreateHumanTaskRequest, context: Context) -> CreateHumanTaskResponse:
    """Create a workflow step that requires human intervention."""
    start_time = time.time()
    principal_id = _get_principal_id_from_context(context)
    tenant = get_current_tenant()

    # Context management
    ctx_manager = get_context_manager()
    ctx_id = context.headers.get("x-context-id") if hasattr(context, "headers") else None
    persistent_ctx = None
    step = None

    try:
        # Create or get persistent context
        persistent_ctx = ctx_manager.get_or_create_context(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            context_id=ctx_id,
            session_type="interactive",
        )

        # Create workflow step for this tool call
        step = ctx_manager.create_workflow_step(
            context_id=persistent_ctx.context_id,
            step_type="create_human_task",
            step_data={
                "request": req.dict(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Create human task in database
        task_id = str(uuid.uuid4())
        due_by = datetime.utcnow() + timedelta(hours=req.due_in_hours) if req.due_in_hours else None

        with get_db_session() as session:
            human_task = ModelHumanTask(
                task_id=task_id,
                context_id=persistent_ctx.context_id,
                step_id=step.step_id,
                task_type=req.task_type,
                title=req.title,
                description=req.description,
                assigned_to=req.assigned_to,
                priority=req.priority,
                due_by=due_by,
                status="pending",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(human_task)
            session.commit()

        # Log activity
        activity_feed.log_activity(
            tenant_id=tenant["tenant_id"],
            principal_id=principal_id,
            action="create_human_task",
            details={
                "task_id": task_id,
                "task_type": req.task_type,
                "title": req.title,
            },
        )

        # Update workflow step
        ctx_manager.update_workflow_step(
            step_id=step.step_id,
            status="completed",
            result_data={
                "task_id": task_id,
                "status": "pending",
                "due_by": due_by.isoformat() if due_by else None,
            },
        )

        log_tool_activity(context, "create_workflow_step_for_task", start_time)

        return CreateHumanTaskResponse(task_id=task_id, status="pending", due_by=due_by)

    except Exception as e:
        logger.error(f"Error creating workflow step for task: {e}")
        
        # Update workflow step with error
        if step:
            ctx_manager.update_workflow_step(
                step_id=step.step_id,
                status="failed",
                error_data={"error": str(e)},
            )
        
        raise


@FastMCP.tool
def get_pending_workflows(req: GetPendingTasksRequest, context: Context) -> GetPendingTasksResponse:
    """Get pending workflow steps that need action."""
    # Check if requester is admin
    principal_id = get_principal_from_context(context)
    tenant = get_current_tenant()
    is_admin = principal_id == f"{tenant['tenant_id']}_admin"

    # Determine owner filter based on role
    owner_filter = None
    if not is_admin:
        # Non-admins only see steps assigned to "principal" role
        owner_filter = "principal"
    elif req.principal_id:
        # Admin filtering by specific principal
        owner_filter = "principal"
    else:
        # Admin can see publisher and system tasks
        owner_filter = req.owner_filter

    try:
        with get_db_session() as session:
            query = session.query(ModelHumanTask).filter_by(status="pending")

            if owner_filter:
                query = query.filter_by(assigned_to=owner_filter)

            if req.task_type:
                query = query.filter_by(task_type=req.task_type)

            if req.limit:
                query = query.limit(req.limit)

            pending_tasks = query.all()

            tasks = []
            for task in pending_tasks:
                tasks.append({
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "title": task.title,
                    "description": task.description,
                    "assigned_to": task.assigned_to,
                    "priority": task.priority,
                    "due_by": task.due_by,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                })

            return GetPendingTasksResponse(tasks=tasks)

    except Exception as e:
        logger.error(f"Error getting pending workflows: {e}")
        raise


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
