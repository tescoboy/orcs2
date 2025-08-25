"""Workflow update operations for A2A protocol support."""

from datetime import UTC, datetime
from typing import Any

from rich.console import Console

from src.core.database.database_session import DatabaseManager
from src.core.database.models import WorkflowStep

console = Console()


class WorkflowUpdates(DatabaseManager):
    """Workflow update operations."""

    def __init__(self):
        super().__init__()

    def update_workflow_step(
        self,
        step_id: str,
        status: str | None = None,
        response_data: dict[str, Any] | None = None,
        error_message: str | None = None,
        transaction_details: dict[str, Any] | None = None,
        add_comment: dict[str, str] | None = None,
    ) -> None:
        """Update a workflow step's status and data.

        Args:
            step_id: The step ID
            status: New status
            response_data: Response/result data
            error_message: Error message if failed
            transaction_details: Actual API calls made
            add_comment: Optional comment to add {user, comment}
        """
        session = self.session
        try:
            step = session.query(WorkflowStep).filter_by(step_id=step_id).first()
            if step:
                if status:
                    step.status = status
                    if status in ["completed", "failed"] and not step.completed_at:
                        step.completed_at = datetime.now(UTC)

                if response_data is not None:
                    step.response_data = response_data
                if error_message is not None:
                    step.error_message = error_message
                if transaction_details is not None:
                    step.transaction_details = transaction_details

                if add_comment:
                    # Ensure comments is a list
                    if not isinstance(step.comments, list):
                        step.comments = []
                    step.comments.append(
                        {
                            "user": add_comment.get("user", "system"),
                            "timestamp": datetime.now(UTC).isoformat(),
                            "text": add_comment.get("text", add_comment.get("comment", "")),
                        }
                    )

                session.commit()
                console.print(f"[green]Updated workflow step {step_id}[/green]")
        finally:
            session.close()


# Singleton instance getter for compatibility
_workflow_updates_instance = None


def get_workflow_updates() -> WorkflowUpdates:
    """Get or create singleton WorkflowUpdates instance."""
    global _workflow_updates_instance
    if _workflow_updates_instance is None:
        _workflow_updates_instance = WorkflowUpdates()
    return _workflow_updates_instance
