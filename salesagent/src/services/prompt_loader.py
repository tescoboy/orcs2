"""Service for loading and compiling AI prompt templates."""

from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from .prompt_loader_core import PromptLoaderCore
from ..core.database.database_session import get_db_session
from ..core.database.models import Tenant


class PromptLoader(PromptLoaderCore):
    """Service for loading tenant-specific AI prompt templates."""
    
    def get_tenant_prompt(self, tenant_id: str) -> str:
        """Get the prompt template for a tenant, falling back to default if not set."""
        with get_db_session() as db:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                raise ValueError(f"Tenant not found: {tenant_id}")
            
            if tenant.ai_prompt_template:
                return tenant.ai_prompt_template
            else:
                return self._get_default_prompt()
    
    def compile_prompt(self, template: str, context: Dict[str, str]) -> str:
        """Compile a prompt template by replacing placeholders with context values."""
        # Validate template first
        is_valid, validation_messages = self.validate_template(template)
        if not is_valid:
            error_messages = [msg for msg in validation_messages if 'Missing required' in msg]
            if error_messages:
                raise ValueError(f"Invalid template: {'; '.join(error_messages)}")
        
        # Replace placeholders (case-insensitive)
        result = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        
        return result


# Convenience function for easy access
def get_tenant_prompt(tenant_id: str) -> str:
    """Get the prompt template for a tenant."""
    loader = PromptLoader()
    return loader.get_tenant_prompt(tenant_id)


def compile_prompt(template: str, context: Dict[str, str]) -> str:
    """Compile a prompt template with context."""
    loader = PromptLoader()
    return loader.compile_prompt(template, context)
