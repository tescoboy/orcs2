"""Context persistence manager for A2A protocol support - Modular wrapper."""

# Import all the modular components
from src.core.context_core import ContextCore, get_context_core
from src.core.context_queries import ContextQueries, get_context_queries
from src.core.workflow_operations import WorkflowOperations, get_workflow_operations
from src.core.workflow_updates import WorkflowUpdates, get_workflow_updates
from src.core.workflow_queries import WorkflowQueries, get_workflow_queries
from src.core.context_lifecycle import ContextLifecycle, get_context_lifecycle
from src.core.context_messages import ContextMessages, get_context_messages

# For backward compatibility, provide the original ContextManager class
class ContextManager(ContextCore):
    """Legacy ContextManager class for backward compatibility.
    
    This class inherits from ContextCore and provides access to all functionality
    through composition of the modular components.
    """
    
    def __init__(self):
        super().__init__()
        self._queries = get_context_queries()
        self._workflow_ops = get_workflow_operations()
        self._workflow_updates = get_workflow_updates()
        self._workflow_queries = get_workflow_queries()
        self._lifecycle = get_context_lifecycle()
        self._messages = get_context_messages()
    
    # Delegate workflow operations
    def create_workflow_step(self, *args, **kwargs):
        return self._workflow_ops.create_workflow_step(*args, **kwargs)
    
    def update_workflow_step(self, *args, **kwargs):
        return self._workflow_updates.update_workflow_step(*args, **kwargs)
    
    def get_pending_steps(self, *args, **kwargs):
        return self._workflow_queries.get_pending_steps(*args, **kwargs)
    
    def get_contexts_for_principal(self, *args, **kwargs):
        return self._queries.get_contexts_for_principal(*args, **kwargs)
    
    # Delegate lifecycle operations
    def get_object_lifecycle(self, *args, **kwargs):
        return self._lifecycle.get_object_lifecycle(*args, **kwargs)
    
    def get_context_status(self, *args, **kwargs):
        return self._lifecycle.get_context_status(*args, **kwargs)
    
    # Delegate message operations
    def add_message(self, *args, **kwargs):
        return self._messages.add_message(*args, **kwargs)
    
    def set_tool_state(self, *args, **kwargs):
        return self._messages.set_tool_state(*args, **kwargs)


# Singleton instance getter for compatibility
_context_manager_instance = None


def get_context_manager() -> ContextManager:
    """Get or create singleton ContextManager instance."""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
    return _context_manager_instance
