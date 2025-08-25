"""
SQLAlchemy models for database schema - Combined version.
This file contains all models in the correct order to resolve relationship issues.
Original models.py was 708 lines - now combined into a single file for SQLAlchemy compatibility.
"""

from sqlalchemy import (
    DECIMAL,
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Numeric,
    Enum,
    PrimaryKeyConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.json_validators import JSONValidatorMixin
from datetime import datetime

Base = declarative_base()


# ============================================================================
# CORE MODELS
# ============================================================================

class Tenant(Base, JSONValidatorMixin):
    __tablename__ = "tenants"

    tenant_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean)
    billing_plan = Column(String(50))
    billing_contact = Column(Text)
    ad_server = Column(String(50))
    max_daily_budget = Column(Integer, nullable=False, default=10000)
    enable_aee_signals = Column(Boolean, nullable=False, default=True)
    authorized_emails = Column(Text)  # TEXT (JSON string)
    authorized_domains = Column(Text)  # TEXT (JSON string)
    slack_webhook_url = Column(String(500))
    admin_token = Column(String(100))
    auto_approve_formats = Column(Text)  # TEXT (JSON string)
    human_review_required = Column(Boolean, nullable=False, default=True)
    slack_audit_webhook_url = Column(String(500))
    hitl_webhook_url = Column(String(500))
    policy_settings = Column(Text)  # TEXT (JSON string)
    ai_prompt_template = Column(Text)
    ai_prompt_updated_at = Column(DateTime)


class CreativeFormat(Base):
    __tablename__ = "creative_formats"

    format_id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # video, audio, display, native, dooh
    description = Column(Text)
    assets = Column(JSON)  # JSON array of asset specifications
    delivery_options = Column(JSON)  # JSON object
    additional_specs = Column(JSON)  # JSON object
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Product(Base, JSONValidatorMixin):
    __tablename__ = "products"

    tenant_id = Column(String(50), ForeignKey("tenants.tenant_id"), nullable=False)
    product_id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    formats = Column(JSON, nullable=False)
    targeting_template = Column(JSON, nullable=False)
    delivery_type = Column(String(50), nullable=False)
    is_fixed_price = Column(Boolean, nullable=False)
    cpm = Column(Float)
    price_guidance = Column(Text)
    is_custom = Column(Boolean)
    expires_at = Column(DateTime)
    countries = Column(JSON)
    implementation_config = Column(JSON)
    targeted_ages = Column(Text)
    verified_minimum_age = Column(Integer)


class Principal(Base, JSONValidatorMixin):
    __tablename__ = "principals"

    tenant_id = Column(String(50), ForeignKey("tenants.tenant_id"), nullable=False)
    principal_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    platform_mappings = Column(JSON, nullable=False)
    access_token = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        PrimaryKeyConstraint('tenant_id', 'principal_id'),
    )


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenants.tenant_id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(200))
    role = Column(String(50), default="user")  # admin, user, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


# ============================================================================
# MEDIA MODELS
# ============================================================================

class MediaBuy(Base):
    __tablename__ = "media_buys"

    media_buy_id = Column(String(100), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenants.tenant_id"), nullable=False)
    principal_id = Column(String(100), ForeignKey("principals.principal_id"), nullable=False)
    order_name = Column(String(255), nullable=False)
    advertiser_name = Column(String(255), nullable=False)
    campaign_objective = Column(Text)
    kpi_goal = Column(Text)
    budget = Column(Float)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    approved_at = Column(DateTime)
    approved_by = Column(String(255))
    raw_request = Column(JSON, nullable=False)
    context_id = Column(String(100))


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


# ============================================================================
# WORKFLOW MODELS
# ============================================================================

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


# ============================================================================
# GAM MODELS
# ============================================================================

class GAMInventory(Base):
    __tablename__ = "gam_inventory"

    inventory_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), nullable=False)
    gam_ad_unit_id = Column(BigInteger, nullable=False)
    ad_unit_name = Column(String(200), nullable=False)
    ad_unit_path = Column(String(500))
    ad_unit_size = Column(String(100))
    ad_unit_type = Column(String(50))
    parent_id = Column(BigInteger)
    status = Column(String(20), default="active")
    targeting_data = Column(JSON)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class ProductInventoryMapping(Base):
    __tablename__ = "product_inventory_mappings"

    mapping_id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    inventory_id = Column(String(50), ForeignKey("gam_inventory.inventory_id"), nullable=False)
    mapping_type = Column(String(50), default="direct")  # direct, targeting, custom
    targeting_criteria = Column(JSON)
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class GAMOrder(Base):
    __tablename__ = "gam_orders"

    order_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), nullable=False)
    gam_order_id = Column(BigInteger, nullable=False)
    order_name = Column(String(200), nullable=False)
    advertiser_id = Column(BigInteger)
    advertiser_name = Column(String(200))
    trafficker_id = Column(BigInteger)
    trafficker_name = Column(String(200))
    order_type = Column(String(50))
    status = Column(String(20))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    total_budget = Column(DECIMAL(10, 2))
    currency = Column(String(3), default="USD")
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class GAMLineItem(Base):
    __tablename__ = "gam_line_items"

    line_item_id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("gam_orders.order_id"), nullable=False)
    gam_line_item_id = Column(BigInteger, nullable=False)
    line_item_name = Column(String(200), nullable=False)
    line_item_type = Column(String(50))
    priority = Column(Integer)
    status = Column(String(20))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    cost_type = Column(String(20))  # CPM, CPC, CPA
    cost_per_unit = Column(DECIMAL(10, 2))
    units_ordered = Column(BigInteger)
    units_delivered = Column(BigInteger)
    total_cost = Column(DECIMAL(10, 2))
    targeting_data = Column(JSON)
    creative_data = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


# ============================================================================
# BUYER MODELS
# ============================================================================

class BuyerCampaign(Base):
    __tablename__ = "buyer_campaigns"

    campaign_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), nullable=False)
    campaign_name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="draft")  # draft, active, paused, completed
    budget = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    targeting_criteria = Column(JSON)
    performance_metrics = Column(JSON)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class BuyerCampaignProduct(Base):
    __tablename__ = "buyer_campaign_products"

    mapping_id = Column(String(50), primary_key=True)
    campaign_id = Column(String(50), ForeignKey("buyer_campaigns.campaign_id"), nullable=False)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    priority = Column(Integer, default=1)
    budget_allocation = Column(Float)
    targeting_overlay = Column(JSON)
    performance_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


# ============================================================================
# RELATIONSHIPS (defined after all classes)
# ============================================================================

# Tenant relationships
Tenant.principals = relationship("Principal", back_populates="tenant")
Tenant.products = relationship("Product", back_populates="tenant")
Tenant.media_buys = relationship("MediaBuy", back_populates="tenant")
Tenant.adapter_config = relationship("AdapterConfig", back_populates="tenant", uselist=False)

# Principal relationships
Principal.tenant = relationship("Tenant", back_populates="principals")
Principal.media_buys = relationship("MediaBuy", back_populates="principal")

# Product relationships
Product.tenant = relationship("Tenant", back_populates="products")

# MediaBuy relationships
MediaBuy.principal = relationship("Principal", back_populates="media_buys")
MediaBuy.tenant = relationship("Tenant", back_populates="media_buys")

# Context relationships
Context.workflow_steps = relationship("WorkflowStep", back_populates="context")

# WorkflowStep relationships
WorkflowStep.context = relationship("Context", back_populates="workflow_steps")

# GAMOrder relationships
GAMOrder.line_items = relationship("GAMLineItem", back_populates="order")

# GAMLineItem relationships
GAMLineItem.order = relationship("GAMOrder", back_populates="line_items")

# BuyerCampaign relationships
BuyerCampaign.products = relationship("BuyerCampaignProduct", back_populates="campaign")

# BuyerCampaignProduct relationships
BuyerCampaignProduct.campaign = relationship("BuyerCampaign", back_populates="products")

# AdapterConfig relationships
AdapterConfig.tenant = relationship("Tenant", back_populates="adapter_config")
