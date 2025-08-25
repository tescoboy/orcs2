"""Workflow query operations for A2A protocol support."""

from src.core.database.database_session import DatabaseManager
from src.core.database.models import WorkflowStep


class WorkflowQueries(DatabaseManager):
    """Workflow query operations."""

    def __init__(self):
        super().__init__()

    def get_pending_steps(self, owner: str | None = None, assigned_to: str | None = None) -> list[WorkflowStep]:
        """Get pending workflow steps from the work queue.

        The owner field tells us who needs to act:
        - 'principal': waiting on the advertiser/buyer
        - 'publisher': waiting on the publisher/seller
        - 'system': automated system processing

        Args:
            owner: Filter by owner (principal, publisher, system)
            assigned_to: Filter by specific assignee

        Returns:
            List of pending WorkflowStep objects
        """
        session = self.session
        try:
            query = session.query(WorkflowStep).filter(WorkflowStep.status.in_(["pending", "requires_approval"]))

            if owner:
                query = query.filter(WorkflowStep.owner == owner)
            if assigned_to:
                query = query.filter(WorkflowStep.assigned_to == assigned_to)

            steps = query.all()
            # Detach all from session
            for step in steps:
                session.expunge(step)
            return steps
        finally:
            session.close()


# Singleton instance getter for compatibility
_workflow_queries_instance = None


def get_workflow_queries() -> WorkflowQueries:
    """Get or create singleton WorkflowQueries instance."""
    global _workflow_queries_instance
    if _workflow_queries_instance is None:
        _workflow_queries_instance = WorkflowQueries()
    return _workflow_queries_instance
