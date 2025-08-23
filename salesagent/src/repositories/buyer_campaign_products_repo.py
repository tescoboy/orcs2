"""Repository for buyer campaign product operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import json

from ..core.database.database_session import get_db_session
from ..core.database.models import BuyerCampaignProduct


class BuyerCampaignProductsRepo:
    """Repository for buyer campaign product operations."""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session or get_db_session()
    
    def add_product_to_campaign(self, campaign_id: int, product_id: str, 
                               publisher_tenant_id: str, source_agent_id: Optional[str],
                               price_cpm: float, quantity: Optional[int], 
                               snapshot: Dict[str, Any]) -> BuyerCampaignProduct:
        """Add a product to a campaign with snapshot."""
        campaign_product = BuyerCampaignProduct(
            campaign_id=campaign_id,
            product_id=product_id,
            publisher_tenant_id=publisher_tenant_id,
            source_agent_id=source_agent_id,
            price_cpm=price_cpm,
            quantity=quantity,
            snapshot_json=json.dumps(snapshot)
        )
        
        self.db_session.add(campaign_product)
        self.db_session.commit()
        self.db_session.refresh(campaign_product)
        
        return campaign_product
    
    def get_products_by_campaign_id(self, campaign_id: int) -> List[BuyerCampaignProduct]:
        """Get all products for a campaign."""
        return self.db_session.query(BuyerCampaignProduct).filter(
            BuyerCampaignProduct.campaign_id == campaign_id
        ).all()
    
    def get_product_by_id(self, product_id: int) -> Optional[BuyerCampaignProduct]:
        """Get a campaign product by ID."""
        return self.db_session.query(BuyerCampaignProduct).filter(
            BuyerCampaignProduct.id == product_id
        ).first()
    
    def update_product_quantity(self, product_id: int, quantity: int) -> bool:
        """Update product quantity."""
        product = self.get_product_by_id(product_id)
        if not product:
            return False
        
        product.quantity = quantity
        self.db_session.commit()
        
        return True
    
    def remove_product_from_campaign(self, product_id: int) -> bool:
        """Remove a product from a campaign."""
        product = self.get_product_by_id(product_id)
        if not product:
            return False
        
        self.db_session.delete(product)
        self.db_session.commit()
        
        return True
    
    def get_campaign_products_summary(self, campaign_id: int) -> Dict[str, Any]:
        """Get summary of products in a campaign."""
        products = self.get_products_by_campaign_id(campaign_id)
        
        total_value = 0
        product_count = len(products)
        publishers = set()
        
        for product in products:
            total_value += product.price_cpm * (product.quantity or 1)
            publishers.add(product.publisher_tenant_id)
        
        return {
            'product_count': product_count,
            'total_value': total_value,
            'publisher_count': len(publishers),
            'publishers': list(publishers)
        }
    
    def get_product_snapshot(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get the product snapshot as a dictionary."""
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        
        try:
            return json.loads(product.snapshot_json)
        except json.JSONDecodeError:
            return None
