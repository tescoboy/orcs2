"""
Media buy and creative SQLAlchemy models.
Extracted from models.py to reduce file size and improve maintainability.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class MediaBuy(Base):
    __tablename__ = "media_buys"

    media_buy_id = Column(String(50), primary_key=True)
    context_id = Column(String(50), unique=True)
    principal_id = Column(String(50), ForeignKey("principals.principal_id"), nullable=False)
    tenant_id = Column(String(50), ForeignKey("tenants.tenant_id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, active, paused, completed, cancelled
    total_budget = Column(Float)
    targeting_overlay = Column(JSON)  # JSON object
    delivery_data = Column(JSON)  # JSON object
    performance_metrics = Column(JSON)  # JSON object
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    principal = relationship("Principal", back_populates="media_buys")
    tenant = relationship("Tenant", back_populates="media_buys")


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String(50), primary_key=True)
    task_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    assigned_to = Column(String(50))
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="pending")
    due_by = Column(DateTime)
    completed_by = Column(String(50))
    completed_at = Column(DateTime)
    completion_notes = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class HumanTask(Base):
    __tablename__ = "human_tasks"

    task_id = Column(String(50), primary_key=True)
    context_id = Column(String(50), nullable=False)
    step_id = Column(String(50), nullable=False)
    task_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    assigned_to = Column(String(50), nullable=False)
    priority = Column(String(20), default="medium")
    due_by = Column(DateTime)
    status = Column(String(20), default="pending")
    completed_by = Column(String(50))
    completed_at = Column(DateTime)
    completion_notes = Column(Text)
    verified_by = Column(String(50))
    verified_at = Column(DateTime)
    verification_notes = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), nullable=False)
    principal_id = Column(String(50))
    user_id = Column(String(50))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(50))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
