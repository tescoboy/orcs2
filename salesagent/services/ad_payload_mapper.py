"""Ad payload mapper service for campaign export."""

from typing import Dict, List, Any, Optional
import json

from .ad_payload_core import AdPayloadCore


class AdPayloadMapper:
    """Service for mapping campaign data to ad payload format."""
    
    @staticmethod
    def map_campaign_to_payload(campaign: Dict[str, Any], products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map campaign and products to ad payload JSON format.
        
        Args:
            campaign: Campaign data dict with campaign details
            products: List of product dicts with snapshots
            
        Returns:
            Dict containing the ad payload in standard format
        """
        # Extract campaign details using core functionality
        campaign_info = AdPayloadCore.extract_campaign_data(campaign)
        
        # Build flight dates
        flight = {
            "start_date": campaign_info["start_date"],
            "end_date": campaign_info["end_date"]
        }
        
        # Build line items from products
        line_items = []
        for product_data in products:
            line_item = AdPayloadCore.extract_line_item_data(product_data)
            line_items.append(line_item)
        
        # Build final payload
        payload = {
            "campaign_name": campaign_info["campaign_name"],
            "objective": campaign_info["objective"],
            "flight": flight,
            "budget_total": campaign_info["budget_total"],
            "line_items": line_items
        }
        
        return payload
    
    @staticmethod
    def format_payload_json(payload: Dict[str, Any], pretty: bool = False) -> str:
        """
        Format payload as JSON string.
        
        Args:
            payload: The payload dictionary
            pretty: Whether to pretty-print with indentation
            
        Returns:
            JSON string representation
        """
        if pretty:
            return json.dumps(payload, indent=2, ensure_ascii=False)
        else:
            return json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    
    @staticmethod
    def generate_filename(campaign_id: int, campaign_name: Optional[str] = None) -> str:
        """
        Generate a safe filename for the payload download.
        
        Args:
            campaign_id: The campaign ID
            campaign_name: Optional campaign name for more descriptive filename
            
        Returns:
            Safe filename string
        """
        # Sanitize campaign name for filename
        if campaign_name:
            # Remove/replace unsafe characters
            safe_name = ''.join(c for c in campaign_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            if safe_name:
                return f"campaign_{campaign_id}_{safe_name}.json"
        
        return f"campaign_{campaign_id}.json"
    
    @staticmethod
    def validate_payload(payload: Dict[str, Any]) -> List[str]:
        """
        Validate payload structure and return any errors.
        
        Args:
            payload: The payload dictionary to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate campaign structure
        errors.extend(AdPayloadCore.validate_campaign_structure(payload))
        
        # Validate line items structure
        if 'line_items' in payload:
            errors.extend(AdPayloadCore.validate_line_items_structure(payload['line_items']))
        
        return errors
