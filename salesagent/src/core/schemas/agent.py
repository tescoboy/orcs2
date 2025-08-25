"""
Agent schemas for configuration and status management
"""
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TIMEOUT = "timeout"


class AgentType(str, Enum):
    """Agent type enumeration"""
    LOCAL_AI = "local_ai"
    MCP = "mcp"
    EXTERNAL = "external"


class AgentConfig(BaseModel):
    """Configuration for an agent"""
    agent_id: str = Field(..., description="Unique agent identifier")
    tenant_id: str = Field(..., description="Tenant this agent belongs to")
    name: str = Field(..., description="Human-readable agent name")
    type: str = Field(..., description="Agent type (local_ai, mcp, external)")
    status: AgentStatus = Field(AgentStatus.ACTIVE, description="Current agent status")
    endpoint_url: Optional[str] = Field(None, description="Agent endpoint URL")
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific configuration")
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    
    class Config:
        use_enum_values = True


class AgentReport(BaseModel):
    """Report for agent execution results"""
    agent_id: str = Field(..., description="Agent identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    status: AgentStatus = Field(..., description="Execution status")
    latency_ms: Optional[int] = Field(None, description="Execution time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    products_count: int = Field(0, description="Number of products returned")
    executed_at: datetime = Field(default_factory=lambda: datetime.now())


class AgentSelectRequest(BaseModel):
    """Request for agent product selection"""
    prompt: str = Field(..., description="Buyer prompt/campaign brief")
    max_results: int = Field(10, description="Maximum number of products to return")
    filters: Optional[Dict[str, Any]] = Field(None, description="Product filters")
    locale: str = Field("en-US", description="Locale for results")
    currency: str = Field("USD", description="Currency for pricing")
    timeout_seconds: int = Field(10, description="Request timeout in seconds")


class AgentSelectResponse(BaseModel):
    """Response from agent product selection"""
    agent_id: str = Field(..., description="Agent identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    products: list = Field(default_factory=list, description="Selected products")
    total_found: int = Field(0, description="Total products found")
    execution_time_ms: int = Field(0, description="Execution time in milliseconds")
    status: AgentStatus = Field(AgentStatus.ACTIVE, description="Execution status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        use_enum_values = True
