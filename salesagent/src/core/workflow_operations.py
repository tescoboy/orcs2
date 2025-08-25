"""Workflow step operations for A2A protocol support."""

import uuid
from datetime import UTC, datetime
from typing import Any

from rich.console import Console

from src.core.database.database_session import DatabaseManager
from src.core.database.models import ObjectWorkflowMapping, WorkflowStep

console = Console()


class WorkflowOperations(DatabaseManager):
    """Workflow step operations for creating and managing workflow steps."""

    def __init__(self):
        super().__init__()

    def create_workflow_step(
        self,
        context_id: str,
        step_type: str,  # tool_call, approval, notification, etc.
        owner: str,  # principal, publisher, system - who needs to act
        status: str = "pending",  # pending, in_progress, completed, failed, requires_approval
        tool_name: str | None = None,
        request_data: dict[str, Any] | None = None,
        response_data: dict[str, Any] | None = None,
        assigned_to: str | None = None,
        error_message: str | None = None,
        transaction_details: dict[str, Any] | None = None,
        object_mappings: list[dict[str, str]] | None = None,
        initial_comment: str | None = None,
    ) -> WorkflowStep:
        """Create a workflow step in the database.

        Args:
            context_id: The context ID
            step_type: Type of step (tool_call, approval, etc.)
            owner: Who needs to act (principal=advertiser, publisher=seller, system=automated)
            status: Step status
            tool_name: Optional tool name if this is a tool call
            request_data: Original request data
            response_data: Response/result data
            assigned_to: Specific user/system if assigned
            error_message: Error message if failed
            transaction_details: Actual API calls made
            object_mappings: List of objects this step relates to [{object_type, object_id, action}]
            initial_comment: Optional initial comment to add

        Returns:
            The created WorkflowStep object
        """
        step_id = f"step_{uuid.uuid4().hex[:12]}"

        # Initialize comments array with initial comment if provided
        comments = []
        if initial_comment:
            comments.append({"user": "system", "timestamp": datetime.now(UTC).isoformat(), "text": initial_comment})

        step = WorkflowStep(
            step_id=step_id,
            context_id=context_id,
            step_type=step_type,
            owner=owner,
            status=status,
            tool_name=tool_name,
            request_data=request_data,
            response_data=response_data,
            assigned_to=assigned_to,
            error_message=error_message,
            transaction_details=transaction_details,
            comments=comments,
            created_at=datetime.now(UTC),
        )

        if status == "completed":
            step.completed_at = datetime.now(UTC)

        session = self.session
        try:
            session.add(step)

            # Create object mappings if provided
            if object_mappings:
                for mapping in object_mappings:
                    obj_mapping = ObjectWorkflowMapping(
                        object_type=mapping["object_type"],
                        object_id=mapping["object_id"],
                        step_id=step_id,
                        action=mapping.get("action", step_type),
                        created_at=datetime.now(UTC),
                    )
                    session.add(obj_mapping)

            session.commit()
            session.refresh(step)
            # Detach from session
            session.expunge(step)
            console.print(f"[green]Created workflow step {step_id} for context {context_id}[/green]")
            return step
        except Exception as e:
            session.rollback()
            console.print(f"[red]Failed to create workflow step: {e}[/red]")
            raise
        finally:
            session.close()






# Singleton instance getter for compatibility
_workflow_operations_instance = None


def get_workflow_operations() -> WorkflowOperations:
    """Get or create singleton WorkflowOperations instance."""
    global _workflow_operations_instance
    if _workflow_operations_instance is None:
        _workflow_operations_instance = WorkflowOperations()
    return _workflow_operations_instance
