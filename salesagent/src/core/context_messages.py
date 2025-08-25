"""Message and state operations for A2A protocol support."""

from datetime import UTC, datetime
from typing import Any

from src.core.database.database_session import DatabaseManager
from src.core.database.models import Context


class ContextMessages(DatabaseManager):
    """Message and state operations for contexts."""

    def __init__(self):
        super().__init__()

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


# Singleton instance getter for compatibility
_context_messages_instance = None


def get_context_messages() -> ContextMessages:
    """Get or create singleton ContextMessages instance."""
    global _context_messages_instance
    if _context_messages_instance is None:
        _context_messages_instance = ContextMessages()
    return _context_messages_instance
