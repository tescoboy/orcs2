"""Context persistence manager for A2A protocol support."""

import uuid
from datetime import UTC, datetime
from typing import Any

from rich.console import Console

from src.core.database.database_session import DatabaseManager
from src.core.database.models import Context, ObjectWorkflowMapping, WorkflowStep

console = Console()


class ContextManager(DatabaseManager):
    """Manages persistent context for conversations and tasks.

    Inherits from DatabaseManager for standardized session management.
    """

    def __init__(self):
        super().__init__()

    def create_context(
        self, tenant_id: str, principal_id: str, initial_conversation: list[dict[str, Any]] | None = None
    ) -> Context:
        """Create a new context for asynchronous operations.

        Note: Synchronous operations don't need a context.
        This is only for async/HITL workflows where we need to track conversation.

        Args:
            tenant_id: The tenant ID
            principal_id: The principal ID
            initial_conversation: Optional initial conversation history

        Returns:
            The created Context object
        """
        context_id = f"ctx_{uuid.uuid4().hex[:12]}"

        context = Context(
            context_id=context_id,
            tenant_id=tenant_id,
            principal_id=principal_id,
            conversation_history=initial_conversation or [],
            last_activity_at=datetime.now(UTC),
        )

        try:
            self.session.add(context)
            self.session.commit()
            console.print(f"[green]Created context {context_id} for principal {principal_id}[/green]")
            # Refresh to get any database-generated values
            self.session.refresh(context)
            # Create a detached copy with all attributes loaded
            context_id = context.context_id
            self.session.expunge(context)
            return context
        except Exception as e:
            self.session.rollback()
            console.print(f"[red]Failed to create context: {e}[/red]")
            raise
        finally:
            # DatabaseManager handles session cleanup differently
            pass

    def get_context(self, context_id: str) -> Context | None:
        """Get a context by ID.

        Args:
            context_id: The context ID

        Returns:
            The Context object or None if not found
        """
        session = self.session
        try:
            context = session.query(Context).filter_by(context_id=context_id).first()
            if context:
                # Detach from session
                session.expunge(context)
            return context
        finally:
            session.close()

    def get_or_create_context(
        self, tenant_id: str, principal_id: str, context_id: str | None = None, is_async: bool = False
    ) -> Context | None:
        """Get existing context or create new one if needed.

        For synchronous operations, returns None.
        For asynchronous operations, returns or creates a context.

        Args:
            tenant_id: The tenant ID
            principal_id: The principal ID
            context_id: Optional existing context ID
            is_async: Whether this is an async operation needing context

        Returns:
            Context object for async operations, None for sync operations
        """
        if not is_async:
            return None

        if context_id:
            return self.get_context(context_id)
        else:
            return self.create_context(tenant_id, principal_id)

    def update_activity(self, context_id: str) -> None:
        """Update the last activity timestamp for a context.

        Args:
            context_id: The context ID
        """
        try:
            context = self.session.query(Context).filter_by(context_id=context_id).first()
            if context:
                context.last_activity_at = datetime.now(UTC)
                self.session.commit()
        finally:
            # DatabaseManager handles session cleanup differently
            pass

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

    def add_message(self, context_id: str, role: str, content: str) -> None:
        """Add a message to the conversation history.

        This is for human-readable messages (clarifications, refinements).
        Tool calls and operational steps go in workflow_steps.

        Args:
            context_id: The context ID
            role: Message role (user, assistant, system)
            content: Message content
        """
        session = self.session
        try:
            context = session.query(Context).filter_by(context_id=context_id).first()
            if context:
                if not isinstance(context.conversation_history, list):
                    context.conversation_history = []

                context.conversation_history.append(
                    {"role": role, "content": content, "timestamp": datetime.now(UTC).isoformat()}
                )
                context.last_activity_at = datetime.now(UTC)
                session.commit()
        finally:
            session.close()

    def set_tool_state(self, context_id: str, tool_name: str, state: dict[str, Any]) -> None:
        """Set the current tool state in a context.

        This is for tracking partial progress within a tool for HITL scenarios.

        Args:
            context_id: The context ID
            tool_name: The tool name
            state: The tool state
        """
        # For now, we can store this in the latest workflow step's response_data
        # or create a dedicated notification step
        pass

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

    def get_contexts_for_principal(self, tenant_id: str, principal_id: str, limit: int = 10) -> list[Context]:
        """Get recent contexts for a principal.

        Args:
            tenant_id: The tenant ID
            principal_id: The principal ID
            limit: Maximum number of contexts to return

        Returns:
            List of Context objects ordered by last activity
        """
        session = self.session
        try:
            contexts = (
                session.query(Context)
                .filter_by(tenant_id=tenant_id, principal_id=principal_id)
                .order_by(Context.last_activity_at.desc())
                .limit(limit)
                .all()
            )

            # Detach all from session
            for context in contexts:
                session.expunge(context)
            return contexts
        finally:
            session.close()


# Singleton instance getter for compatibility
_context_manager_instance = None


def get_context_manager() -> ContextManager:
    """Get or create singleton ContextManager instance."""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
    return _context_manager_instance
