"""
Core task management operations (under 150 lines).
Extracted from task_management.py to maintain the 150-line limit.
"""

import logging
import time
import uuid
from datetime import datetime, timedelta

from fastmcp import FastMCP
from fastmcp.server.context import Context

from src.core.audit_logger import get_audit_logger
from src.core.config_loader import get_current_tenant
from src.core.context_manager import get_context_manager
from src.core.database.database_session import get_db_session
from src.core.database.models import HumanTask as ModelHumanTask
from src.core.schemas import (
    CreateHumanTaskRequest,
    CreateHumanTaskResponse,
    GetPendingTasksRequest,
    GetPendingTasksResponse,
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
