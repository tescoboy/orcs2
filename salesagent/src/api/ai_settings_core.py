"""Core AI settings management functionality."""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from ..core.database.database_session import get_db_session
from ..core.database.models import Tenant
from ..services.prompt_loader import PromptLoader


class AISettingsCore:
    """Core functionality for managing AI settings."""
    
    def __init__(self):
        self.prompt_loader = PromptLoader()
    
    def get_tenant_and_prompt(self, tenant_id: str) -> Tuple[Tenant, str]:
        """Get tenant and their current prompt template."""
        with get_db_session() as db:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                raise ValueError(f"Tenant not found: {tenant_id}")
            
            current_prompt = tenant.ai_prompt_template or self.prompt_loader._get_default_prompt()
            return tenant, current_prompt
    
    def save_tenant_prompt(self, tenant_id: str, template: str) -> Tuple[bool, List[str]]:
        """Save a custom prompt template for a tenant."""
        try:
            # Validate the template
            is_valid, validation_messages = self.prompt_loader.validate_template(template)
            if not is_valid:
                error_messages = [msg for msg in validation_messages if 'Missing required' in msg]
                return False, error_messages
            
            # Save to database
            with get_db_session() as db:
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if not tenant:
                    return False, [f"Tenant not found: {tenant_id}"]
                
                tenant.ai_prompt_template = template
                tenant.ai_prompt_updated_at = datetime.utcnow()
                db.commit()
                
                return True, []
                
        except Exception as e:
            return False, [f"Error saving template: {str(e)}"]
    
    def reset_tenant_prompt(self, tenant_id: str) -> Tuple[bool, List[str]]:
        """Reset tenant prompt template to default (set to NULL)."""
        try:
            with get_db_session() as db:
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if not tenant:
                    return False, [f"Tenant not found: {tenant_id}"]
                
                tenant.ai_prompt_template = None
                tenant.ai_prompt_updated_at = datetime.utcnow()
                db.commit()
                
                return True, []
                
        except Exception as e:
            return False, [f"Error resetting template: {str(e)}"]
    
    def preview_prompt_compilation(self, template: str, sample_context: Dict[str, str]) -> Tuple[bool, List[str], Optional[str]]:
        """Preview how a template would be compiled with sample context."""
        try:
            compiled = self.prompt_loader.compile_prompt(template, sample_context)
            return True, [], compiled
        except Exception as e:
            return False, [f"Compilation failed: {str(e)}"], None
