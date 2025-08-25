"""
Google Ad Manager integration SQLAlchemy models.
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
    BigInteger,
    DECIMAL,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


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

    # Relationships
    line_items = relationship("GAMLineItem", back_populates="order", lazy="dynamic")


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

    # Relationships
    order = relationship("GAMOrder", back_populates="line_items")
