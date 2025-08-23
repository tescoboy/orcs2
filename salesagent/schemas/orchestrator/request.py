"""Orchestrator request schemas."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class BuyerOrchestrateRequest(BaseModel):
    """Request schema for buyer orchestration."""
    
    prompt: str
    max_results: int = 50
    include_tenant_ids: Optional[List[str]] = None
    exclude_tenant_ids: Optional[List[str]] = None
    include_agent_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    locale: Optional[str] = None
    currency: Optional[str] = None 
