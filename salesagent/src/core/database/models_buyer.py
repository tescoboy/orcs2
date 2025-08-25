"""
Buyer campaign SQLAlchemy models.
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

    # Relationships
    products = relationship("BuyerCampaignProduct", back_populates="campaign", lazy="dynamic")


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

    # Relationships
    campaign = relationship("BuyerCampaign", back_populates="products")
