"""Test payload mapper shape and structure."""

import pytest
from datetime import date
from services.ad_payload_mapper import AdPayloadMapper


class TestPayloadMapperShape:
    """Test payload mapper produces correct structure."""
    
    def test_map_campaign_to_payload_basic_structure(self):
        """Test basic payload structure with realistic data."""
        # Mock campaign data
        campaign = {
            'campaign': type('Campaign', (), {
                'name': 'Test Campaign',
                'objective': 'Reach tech enthusiasts',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31),
                'budget_total': 10000.0
            })()
        }
        
        # Mock products with snapshots
        products = [
            {
                'campaign_product': type('CampaignProduct', (), {
                    'publisher_tenant_id': 'pub1',
                    'product_id': 'prod1',
                    'source_agent_id': 'agent1',
                    'price_cpm': 5.50,
                    'quantity': 1000
                })(),
                'snapshot': {
                    'name': 'Tech Banner Ad',
                    'publisher_name': 'Tech Publisher',
                    'delivery_type': 'guaranteed',
                    'formats': ['display', 'banner'],
                    'image_url': 'https://example.com/image.jpg',
                    'rationale': 'Perfect for tech campaigns'
                }
            },
            {
                'campaign_product': type('CampaignProduct', (), {
                    'publisher_tenant_id': 'pub2',
                    'product_id': 'prod2',
                    'source_agent_id': 'agent2',
                    'price_cpm': 12.00,
                    'quantity': None
                })(),
                'snapshot': {
                    'name': 'Video Ad Slot',
                    'publisher_name': 'Video Publisher',
                    'delivery_type': 'non_guaranteed',
                    'formats': ['video'],
                    'image_url': None,
                    'rationale': 'Great video reach'
                }
            }
        ]
        
        # Map to payload
        payload = AdPayloadMapper.map_campaign_to_payload(campaign, products)
        
        # Assert top-level structure
        assert isinstance(payload, dict)
        assert 'campaign_name' in payload
        assert 'objective' in payload
        assert 'flight' in payload
        assert 'budget_total' in payload
        assert 'line_items' in payload
        
        # Assert campaign data
        assert payload['campaign_name'] == 'Test Campaign'
        assert payload['objective'] == 'Reach tech enthusiasts'
        assert payload['budget_total'] == 10000.0
        
        # Assert flight structure
        flight = payload['flight']
        assert isinstance(flight, dict)
        assert flight['start_date'] == '2024-01-01'
        assert flight['end_date'] == '2024-01-31'
        
        # Assert line items
        line_items = payload['line_items']
        assert isinstance(line_items, list)
        assert len(line_items) == 2
        
        # Assert first line item
        item1 = line_items[0]
        assert item1['publisher_tenant_id'] == 'pub1'
        assert item1['product_id'] == 'prod1'
        assert item1['source_agent_id'] == 'agent1'
        assert item1['price_cpm'] == 5.50
        assert item1['quantity'] == 1000
        
        # Assert first line item snapshot
        snapshot1 = item1['snapshot']
        assert snapshot1['name'] == 'Tech Banner Ad'
        assert snapshot1['publisher_name'] == 'Tech Publisher'
        assert snapshot1['delivery_type'] == 'guaranteed'
        assert snapshot1['formats'] == ['display', 'banner']
        assert snapshot1['image_url'] == 'https://example.com/image.jpg'
        assert snapshot1['merchandising_blurb'] == 'Perfect for tech campaigns'
        
        # Assert second line item
        item2 = line_items[1]
        assert item2['publisher_tenant_id'] == 'pub2'
        assert item2['product_id'] == 'prod2'
        assert item2['source_agent_id'] == 'agent2'
        assert item2['price_cpm'] == 12.00
        assert item2['quantity'] is None
    
    def test_format_payload_json_pretty(self):
        """Test JSON formatting with pretty print."""
        payload = {
            'campaign_name': 'Test',
            'line_items': [{'id': 1}, {'id': 2}]
        }
        
        pretty_json = AdPayloadMapper.format_payload_json(payload, pretty=True)
        
        assert '\n' in pretty_json  # Should have newlines
        assert '  ' in pretty_json  # Should have indentation
        assert '"campaign_name": "Test"' in pretty_json
    
    def test_format_payload_json_compact(self):
        """Test JSON formatting without pretty print."""
        payload = {
            'campaign_name': 'Test',
            'line_items': [{'id': 1}, {'id': 2}]
        }
        
        compact_json = AdPayloadMapper.format_payload_json(payload, pretty=False)
        
        assert '\n' not in compact_json  # Should not have newlines
        assert '  ' not in compact_json  # Should not have extra spaces
        assert '"campaign_name":"Test"' in compact_json
    
    def test_generate_filename_with_campaign_name(self):
        """Test filename generation with campaign name."""
        filename = AdPayloadMapper.generate_filename(123, "My Test Campaign")
        assert filename == "campaign_123_My_Test_Campaign.json"
    
    def test_generate_filename_without_campaign_name(self):
        """Test filename generation without campaign name."""
        filename = AdPayloadMapper.generate_filename(123)
        assert filename == "campaign_123.json"
    
    def test_generate_filename_sanitizes_special_characters(self):
        """Test filename generation sanitizes special characters."""
        filename = AdPayloadMapper.generate_filename(123, "Test/Campaign<>:\"Campaign|?*")
        assert filename == "campaign_123_TestCampaignCampaign.json"
