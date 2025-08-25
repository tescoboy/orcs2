"""Core context operations for A2A protocol support."""

import uuid
from datetime import UTC, datetime
from typing import Any

from rich.console import Console

from src.core.database.database_session import DatabaseManager
from src.core.database.models import Context

console = Console()


class ContextCore(DatabaseManager):
    """Core context operations for creating and managing contexts."""

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




# Singleton instance getter for compatibility
_context_core_instance = None


def get_context_core() -> ContextCore:
    """Get or create singleton ContextCore instance."""
    global _context_core_instance
    if _context_core_instance is None:
        _context_core_instance = ContextCore()
    return _context_core_instance
