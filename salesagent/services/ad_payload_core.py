"""Core ad payload mapping functionality."""

import json
from typing import Dict, List, Any, Optional


class AdPayloadCore:
    """Core functionality for ad payload mapping."""
    
    @staticmethod
    def extract_campaign_data(campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize campaign data."""
        campaign_data = campaign.get('campaign', campaign)
        
        # Helper function to get attribute from object or dict
        def get_field(obj, field, default=None):
            if hasattr(obj, field):
                return getattr(obj, field)
            elif hasattr(obj, 'get'):
                return obj.get(field, default)
            else:
                return default
        
        # Extract start_date
        start_date = get_field(campaign_data, 'start_date')
        if hasattr(start_date, 'strftime'):
            start_date_str = start_date.strftime('%Y-%m-%d')
        else:
            start_date_str = str(start_date) if start_date else ''
        
        # Extract end_date
        end_date = get_field(campaign_data, 'end_date')
        if hasattr(end_date, 'strftime'):
            end_date_str = end_date.strftime('%Y-%m-%d')
        else:
            end_date_str = str(end_date) if end_date else ''
        
        return {
            "campaign_name": get_field(campaign_data, 'name', ''),
            "objective": get_field(campaign_data, 'objective'),
            "budget_total": float(get_field(campaign_data, 'budget_total', 0)),
            "start_date": start_date_str,
            "end_date": end_date_str
        }
    
    @staticmethod
    def extract_line_item_data(product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize line item data from product."""
        # Helper function to get attribute from object or dict
        def get_field(obj, field, default=None):
            if hasattr(obj, field):
                return getattr(obj, field)
            elif hasattr(obj, 'get'):
                return obj.get(field, default)
            else:
                return default
        
        # Handle both direct product data and products_with_snapshots format
        if 'campaign_product' in product_data and 'snapshot' in product_data:
            campaign_product = product_data['campaign_product']
            snapshot = product_data['snapshot']
        else:
            # Direct product format
            campaign_product = product_data
            snapshot_json = get_field(product_data, 'snapshot_json', '{}')
            if isinstance(snapshot_json, str):
                snapshot = json.loads(snapshot_json)
            else:
                snapshot = get_field(product_data, 'snapshot', {})
        
        return {
            "publisher_tenant_id": get_field(campaign_product, 'publisher_tenant_id', ''),
            "product_id": get_field(campaign_product, 'product_id', ''),
            "source_agent_id": get_field(campaign_product, 'source_agent_id'),
            "price_cpm": float(get_field(campaign_product, 'price_cpm', 0)),
            "quantity": get_field(campaign_product, 'quantity'),
            "snapshot": {
                "name": snapshot.get('name', '') if snapshot else '',
                "publisher_name": snapshot.get('publisher_name') if snapshot else None,
                "delivery_type": snapshot.get('delivery_type', '') if snapshot else '',
                "formats": snapshot.get('formats', []) if snapshot else [],
                "image_url": snapshot.get('image_url') if snapshot else None,
                "merchandising_blurb": snapshot.get('rationale') if snapshot else None  # Map rationale to merchandising_blurb
            }
        }
    
    @staticmethod
    def validate_campaign_structure(payload: Dict[str, Any]) -> List[str]:
        """Validate campaign-level payload structure."""
        errors = []
        
        # Check required top-level fields
        required_fields = ['campaign_name', 'flight', 'budget_total', 'line_items']
        for field in required_fields:
            if field not in payload:
                errors.append(f"Missing required field: {field}")
        
        # Check flight structure
        if 'flight' in payload:
            flight = payload['flight']
            if not isinstance(flight, dict):
                errors.append("Flight must be an object")
            else:
                for date_field in ['start_date', 'end_date']:
                    if date_field not in flight:
                        errors.append(f"Missing flight.{date_field}")
        
        return errors
    
    @staticmethod
    def validate_line_items_structure(line_items: List[Dict[str, Any]]) -> List[str]:
        """Validate line items structure."""
        errors = []
        
        if not isinstance(line_items, list):
            errors.append("line_items must be an array")
            return errors
        
        for i, item in enumerate(line_items):
            if not isinstance(item, dict):
                errors.append(f"line_items[{i}] must be an object")
                continue
            
            # Check required line item fields
            item_required = ['publisher_tenant_id', 'product_id', 'price_cpm', 'snapshot']
            for field in item_required:
                if field not in item:
                    errors.append(f"line_items[{i}] missing required field: {field}")
            
            # Check snapshot structure
            if 'snapshot' in item and isinstance(item['snapshot'], dict):
                snapshot = item['snapshot']
                snapshot_required = ['name', 'delivery_type', 'formats']
                for field in snapshot_required:
                    if field not in snapshot:
                        errors.append(f"line_items[{i}].snapshot missing required field: {field}")
        
        return errors
