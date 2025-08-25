"""
Workflow and context SQLAlchemy models.
Extracted from models.py to reduce file size and improve maintainability.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.json_validators import JSONValidatorMixin

Base = declarative_base()


class SuperadminConfig(Base):
    __tablename__ = "superadmin_config"

    config_id = Column(String(50), primary_key=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(JSON)
    description = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class AdapterConfig(Base):
    __tablename__ = "adapter_config"

    config_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenants.tenant_id"), nullable=False)
    adapter_type = Column(String(50), nullable=False)  # mock, google_ad_manager, kevel, triton
    config_data = Column(JSON)  # JSON object with adapter-specific configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    job_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), nullable=False)
    job_type = Column(String(50), nullable=False)  # inventory, orders, creatives
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    total_items = Column(Integer)
    processed_items = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Context(Base):
    __tablename__ = "contexts"

    context_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), nullable=False)
    principal_id = Column(String(50), nullable=False)
    session_type = Column(String(50), default="interactive")  # interactive, automated, batch
    session_data = Column(JSON)  # JSON object with session-specific data
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime)

    # Relationships
    workflow_steps = relationship("WorkflowStep", back_populates="context", lazy="dynamic")


class WorkflowStep(Base, JSONValidatorMixin):
    __tablename__ = "workflow_steps"

    step_id = Column(String(50), primary_key=True)
    context_id = Column(String(50), ForeignKey("contexts.context_id"), nullable=False)
    step_type = Column(String(50), nullable=False)  # create_media_buy, add_creative_assets, etc.
    step_data = Column(JSON)  # JSON object with step-specific data
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    result_data = Column(JSON)  # JSON object with step results
    error_data = Column(JSON)  # JSON object with error details
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    context = relationship("Context", back_populates="workflow_steps")


class ObjectWorkflowMapping(Base):
    __tablename__ = "object_workflow_mappings"

    mapping_id = Column(String(50), primary_key=True)
    object_type = Column(String(50), nullable=False)  # media_buy, creative, task
    object_id = Column(String(50), nullable=False)
    workflow_id = Column(String(50), nullable=False)
    step_number = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
