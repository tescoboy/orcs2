"""Object lifecycle and context status operations for A2A protocol support."""

from typing import Any

from src.core.database.database_session import DatabaseManager
from src.core.database.models import ObjectWorkflowMapping, WorkflowStep


class ContextLifecycle(DatabaseManager):
    """Object lifecycle and context status operations."""

    def __init__(self):
        super().__init__()

    def get_object_lifecycle(self, object_type: str, object_id: str) -> list[dict[str, Any]]:
        """Get all workflow steps for an object's lifecycle.

        Args:
            object_type: Type of object (media_buy, creative, product, etc.)
            object_id: The object's ID

        Returns:
            List of workflow steps with their details
        """
        session = self.session
        try:
            # Query object mappings to find all related steps
            mappings = (
                session.query(ObjectWorkflowMapping)
                .filter_by(object_type=object_type, object_id=object_id)
                .order_by(ObjectWorkflowMapping.created_at)
                .all()
            )

            lifecycle = []
            for mapping in mappings:
                step = session.query(WorkflowStep).filter_by(step_id=mapping.step_id).first()
                if step:
                    lifecycle.append(
                        {
                            "step_id": step.step_id,
                            "action": mapping.action,
                            "step_type": step.step_type,
                            "status": step.status,
                            "owner": step.owner,
                            "assigned_to": step.assigned_to,
                            "created_at": step.created_at.isoformat() if step.created_at else None,
                            "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                            "tool_name": step.tool_name,
                            "error_message": step.error_message,
                            "comments": step.comments,
                        }
                    )

            return lifecycle
        finally:
            session.close()

    def get_context_status(self, context_id: str) -> dict[str, Any]:
        """Get the overall status of a context by checking its workflow steps.

        Status is derived from the workflow steps, not stored in context itself.

        Args:
            context_id: The context ID

        Returns:
            Status information derived from workflow steps
        """
        session = self.session
        try:
            steps = session.query(WorkflowStep).filter_by(context_id=context_id).all()

            if not steps:
                return {"status": "no_steps", "summary": "No workflow steps created"}

            # Count steps by status
            status_counts = {"pending": 0, "in_progress": 0, "requires_approval": 0, "completed": 0, "failed": 0}

            for step in steps:
                if step.status in status_counts:
                    status_counts[step.status] += 1

            # Determine overall status
            if status_counts["failed"] > 0:
                overall_status = "has_failures"
            elif status_counts["requires_approval"] > 0:
                overall_status = "awaiting_approval"
            elif status_counts["pending"] > 0 or status_counts["in_progress"] > 0:
                overall_status = "pending_steps"
            else:
                overall_status = "all_completed"

            return {"status": overall_status, "counts": status_counts, "total_steps": len(steps)}
        finally:
            session.close()


# Singleton instance getter for compatibility
_context_lifecycle_instance = None


def get_context_lifecycle() -> ContextLifecycle:
    """Get or create singleton ContextLifecycle instance."""
    global _context_lifecycle_instance
    if _context_lifecycle_instance is None:
        _context_lifecycle_instance = ContextLifecycle()
    return _context_lifecycle_instance
