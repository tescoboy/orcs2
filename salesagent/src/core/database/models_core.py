"""
Core SQLAlchemy models for database schema.
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


class Tenant(Base, JSONValidatorMixin):
    __tablename__ = "tenants"

    tenant_id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    billing_plan = Column(String(50), default="standard")
    billing_contact = Column(String(255))

    # New columns from migration
    ad_server = Column(String(50))
    max_daily_budget = Column(Integer, nullable=False, default=10000)
    enable_aee_signals = Column(Boolean, nullable=False, default=True)
    authorized_emails = Column(JSON)  # JSON array
    authorized_domains = Column(JSON)  # JSON array
    auto_approve_formats = Column(JSON)  # JSON array
    policy_settings = Column(JSON)  # JSON object
    human_review_required = Column(Boolean, nullable=False, default=True)
    admin_token = Column(String(255))

    # Relationships - using strings to avoid circular imports
    principals = relationship("Principal", back_populates="tenant", lazy="dynamic")
    products = relationship("Product", back_populates="tenant", lazy="dynamic")
    media_buys = relationship("MediaBuy", back_populates="tenant", lazy="dynamic")


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

    product_id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    tenant_id = Column(String(50), ForeignKey("tenants.tenant_id"), nullable=False)
    cpm = Column(Integer, nullable=False)  # Cost per thousand impressions in cents
    formats = Column(JSON)  # JSON array of format IDs
    targeting_template = Column(JSON)  # JSON object
    delivery_type = Column(String(50), default="standard")
    is_fixed_price = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships - using strings to avoid circular imports
    tenant = relationship("Tenant", back_populates="products")


class Principal(Base, JSONValidatorMixin):
    __tablename__ = "principals"

    principal_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenants.tenant_id"), nullable=False)
    access_token = Column(String(255), nullable=False)
    platform_mappings = Column(JSON)  # JSON object
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships - using strings to avoid circular imports
    tenant = relationship("Tenant", back_populates="principals")
    media_buys = relationship("MediaBuy", back_populates="principal", lazy="dynamic")


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
