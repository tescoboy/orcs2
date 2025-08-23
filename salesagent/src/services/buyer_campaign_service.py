"""Service for buyer campaign operations."""

from typing import List, Dict, Any, Optional
from datetime import date
import json

from ..repositories.buyer_campaigns_repo import BuyerCampaignsRepo
from ..repositories.buyer_campaign_products_repo import BuyerCampaignProductsRepo
from services.buyer_session import list_selection, clear_selection


class BuyerCampaignService:
    """Service for buyer campaign operations."""
    
    def __init__(self):
        self.campaigns_repo = BuyerCampaignsRepo()
        self.products_repo = BuyerCampaignProductsRepo()
    
    def create_draft_campaign(self, name: str, objective: Optional[str], 
                            start_date: date, end_date: date, 
                            budget_total: float) -> int:
        """Create a draft campaign and return the campaign ID."""
        campaign = self.campaigns_repo.create_campaign(
            name=name,
            objective=objective,
            budget_total=budget_total,
            start_date=start_date,
            end_date=end_date
        )
        
        return campaign.id
    
    def attach_selected_products(self, campaign_id: int, session_id: str) -> bool:
        """Attach products from buyer session to the campaign."""
        # Get selected products from session
        selected_products = list_selection(session_id)
        
        if not selected_products:
            return False
        
        # Create minimal snapshot for each product
        for product in selected_products:
            snapshot = {
                'id': product['id'],
                'name': product['name'],
                'description': product.get('description', ''),
                'image_url': product.get('image_url'),
                'publisher_name': product['publisher_name'],
                'publisher_tenant_id': product['publisher_tenant_id'],
                'delivery_type': product['delivery_type'],
                'formats': product.get('formats', []),
                'categories': product.get('categories', []),
                'targeting': product.get('targeting', {}),
                'rationale': product.get('rationale', ''),
                'score': product.get('score'),
                'source_agent_id': product.get('source_agent_id')
            }
            
            # Add to campaign
            self.products_repo.add_product_to_campaign(
                campaign_id=campaign_id,
                product_id=product['id'],
                publisher_tenant_id=product['publisher_tenant_id'],
                source_agent_id=product.get('source_agent_id'),
                price_cpm=product['price_cpm'],
                quantity=1,  # Default quantity
                snapshot=snapshot
            )
        
        return True
    
    def finalize_campaign(self, campaign_id: int, session_id: str) -> bool:
        """Finalize campaign by attaching products and setting status to active."""
        # Attach selected products
        if not self.attach_selected_products(campaign_id, session_id):
            return False
        
        # Update status to active
        if not self.campaigns_repo.update_campaign_status(campaign_id, 'active'):
            return False
        
        # Clear the buyer session
        clear_selection(session_id)
        
        return True
    
    def get_campaign_summary(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """Get campaign summary with products and totals."""
        summary = self.campaigns_repo.get_campaign_summary(campaign_id)
        if not summary:
            return None
        
        # Add product details with snapshots
        products_with_snapshots = []
        for product in summary['products']:
            snapshot = self.products_repo.get_product_snapshot(product.id)
            if snapshot:
                products_with_snapshots.append({
                    'campaign_product': product,
                    'snapshot': snapshot
                })
        
        summary['products_with_snapshots'] = products_with_snapshots
        
        return summary
    
    def validate_campaign_data(self, name: str, start_date: date, 
                             end_date: date, budget_total: float) -> List[str]:
        """Validate campaign data and return list of errors."""
        errors = []
        
        if not name or not name.strip():
            errors.append("Campaign name is required")
        
        if start_date >= end_date:
            errors.append("End date must be after start date")
        
        if budget_total <= 0:
            errors.append("Budget must be greater than zero")
        
        return errors
    
    def get_campaign_products_summary(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """Get summary of products in a campaign."""
        return self.products_repo.get_campaign_products_summary(campaign_id)
