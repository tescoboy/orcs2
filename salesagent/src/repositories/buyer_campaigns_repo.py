"""Repository for buyer campaign operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, datetime

from ..core.database.database_session import get_db_session
from ..core.database.models import BuyerCampaign


class BuyerCampaignsRepo:
    """Repository for buyer campaign operations."""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session or get_db_session()
    
    def create_campaign(self, name: str, objective: Optional[str], 
                       budget_total: float, start_date: date, end_date: date) -> BuyerCampaign:
        """Create a new buyer campaign."""
        campaign = BuyerCampaign(
            name=name,
            objective=objective,
            budget_total=budget_total,
            start_date=start_date,
            end_date=end_date,
            status='draft'
        )
        
        self.db_session.add(campaign)
        self.db_session.commit()
        self.db_session.refresh(campaign)
        
        return campaign
    
    def get_campaign_by_id(self, campaign_id: int) -> Optional[BuyerCampaign]:
        """Get a campaign by ID."""
        return self.db_session.query(BuyerCampaign).filter(
            BuyerCampaign.id == campaign_id
        ).first()
    
    def update_campaign_status(self, campaign_id: int, status: str) -> bool:
        """Update campaign status."""
        campaign = self.get_campaign_by_id(campaign_id)
        if not campaign:
            return False
        
        campaign.status = status
        campaign.updated_at = datetime.utcnow()
        self.db_session.commit()
        
        return True
    
    def list_campaigns(self, status: Optional[str] = None, 
                      limit: int = 50, offset: int = 0) -> List[BuyerCampaign]:
        """List campaigns with optional status filter."""
        query = self.db_session.query(BuyerCampaign)
        
        if status:
            query = query.filter(BuyerCampaign.status == status)
        
        return query.order_by(desc(BuyerCampaign.created_at)).offset(offset).limit(limit).all()
    
    def delete_campaign(self, campaign_id: int) -> bool:
        """Delete a campaign and its products."""
        campaign = self.get_campaign_by_id(campaign_id)
        if not campaign:
            return False
        
        self.db_session.delete(campaign)
        self.db_session.commit()
        
        return True
    
    def get_campaign_summary(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """Get campaign summary with product count and total value."""
        campaign = self.get_campaign_by_id(campaign_id)
        if not campaign:
            return None
        
        # Get product count and total value
        from .buyer_campaign_products_repo import BuyerCampaignProductsRepo
        products_repo = BuyerCampaignProductsRepo(self.db_session)
        products = products_repo.get_products_by_campaign_id(campaign_id)
        
        total_value = sum(p.price_cpm * (p.quantity or 1) for p in products)
        product_count = len(products)
        
        return {
            'campaign': campaign,
            'product_count': product_count,
            'total_value': total_value,
            'products': products
        }
