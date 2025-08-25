"""Context query operations for A2A protocol support."""

from src.core.database.database_session import DatabaseManager
from src.core.database.models import Context


class ContextQueries(DatabaseManager):
    """Context query operations."""

    def __init__(self):
        super().__init__()

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
_context_queries_instance = None


def get_context_queries() -> ContextQueries:
    """Get or create singleton ContextQueries instance."""
    global _context_queries_instance
    if _context_queries_instance is None:
        _context_queries_instance = ContextQueries()
    return _context_queries_instance
