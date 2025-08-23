"""Test payload JSON route functionality."""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask
from api.buyer_payload_router import buyer_payload_bp


class TestPayloadJsonRoute:
    """Test payload JSON route functionality."""
    
    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        app.register_blueprint(buyer_payload_bp)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    @patch('api.buyer_payload_router.campaign_service.get_campaign_summary')
    @patch('api.buyer_payload_router.payload_mapper.map_campaign_to_payload')
    @patch('api.buyer_payload_router.payload_mapper.validate_payload')
    def test_get_payload_json_success(self, mock_validate, mock_map, mock_summary, client):
        """Test GET /buyer/campaign/{id}/payload.json returns valid JSON."""
        # Mock campaign summary
        mock_summary.return_value = {
            'campaign': MagicMock(name='Test Campaign'),
            'products_with_snapshots': []
        }
        
        # Mock payload mapping
        mock_payload = {
            'campaign_name': 'Test Campaign',
            'objective': 'Test objective',
            'flight': {'start_date': '2024-01-01', 'end_date': '2024-01-31'},
            'budget_total': 1000.0,
            'line_items': []
        }
        mock_map.return_value = mock_payload
        mock_validate.return_value = []  # No errors
        
        response = client.get('/buyer/campaign/123/payload.json')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        # Parse JSON response
        data = json.loads(response.data)
        assert data['campaign_name'] == 'Test Campaign'
        assert data['objective'] == 'Test objective'
        assert 'flight' in data
        assert 'line_items' in data
    
    @patch('api.buyer_payload_router.campaign_service.get_campaign_summary')
    @patch('api.buyer_payload_router.payload_mapper.map_campaign_to_payload')
    @patch('api.buyer_payload_router.payload_mapper.validate_payload')
    def test_get_payload_json_with_download(self, mock_validate, mock_map, mock_summary, client):
        """Test GET /buyer/campaign/{id}/payload.json?download=1 sets download headers."""
        # Mock campaign summary
        mock_campaign = MagicMock()
        mock_campaign.name = 'Test Campaign'
        mock_summary.return_value = {
            'campaign': mock_campaign,
            'products_with_snapshots': []
        }
        
        # Mock payload mapping
        mock_payload = {
            'campaign_name': 'Test Campaign',
            'line_items': []
        }
        mock_map.return_value = mock_payload
        mock_validate.return_value = []  # No errors
        
        response = client.get('/buyer/campaign/123/payload.json?download=1')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert 'Content-Disposition' in response.headers
        assert 'attachment' in response.headers['Content-Disposition']
        assert 'campaign_123' in response.headers['Content-Disposition']
    
    @patch('api.buyer_payload_router.campaign_service.get_campaign_summary')
    def test_get_payload_json_campaign_not_found(self, mock_summary, client):
        """Test GET /buyer/campaign/{id}/payload.json returns 404 for missing campaign."""
        mock_summary.return_value = None
        
        response = client.get('/buyer/campaign/999/payload.json')
        
        assert response.status_code == 404
    
    @patch('api.buyer_payload_router.campaign_service.get_campaign_summary')
    @patch('api.buyer_payload_router.payload_mapper.map_campaign_to_payload')
    @patch('api.buyer_payload_router.payload_mapper.validate_payload')
    def test_get_payload_json_validation_errors(self, mock_validate, mock_map, mock_summary, client):
        """Test GET /buyer/campaign/{id}/payload.json returns 500 for validation errors."""
        # Mock campaign summary
        mock_summary.return_value = {
            'campaign': MagicMock(),
            'products_with_snapshots': []
        }
        
        # Mock payload mapping
        mock_map.return_value = {}
        mock_validate.return_value = ['Missing required field: campaign_name']
        
        response = client.get('/buyer/campaign/123/payload.json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid payload' in data['error']
        assert 'details' in data
    
    @patch('api.buyer_payload_router.campaign_service.get_campaign_summary')
    @patch('api.buyer_payload_router.payload_mapper.map_campaign_to_payload')
    @patch('api.buyer_payload_router.payload_mapper.validate_payload')
    def test_validate_payload_route_success(self, mock_validate, mock_map, mock_summary, client):
        """Test GET /buyer/campaign/{id}/payload/validate returns validation status."""
        # Mock campaign summary
        mock_summary.return_value = {
            'campaign': MagicMock(),
            'products_with_snapshots': []
        }
        
        # Mock payload mapping
        mock_payload = {
            'campaign_name': 'Test Campaign',
            'line_items': [{'id': 1}, {'id': 2}]
        }
        mock_map.return_value = mock_payload
        mock_validate.return_value = []  # No errors
        
        response = client.get('/buyer/campaign/123/payload/validate')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] is True
        assert data['errors'] == []
        assert data['line_items_count'] == 2
        assert data['campaign_name'] == 'Test Campaign'
    
    @patch('api.buyer_payload_router.campaign_service.get_campaign_summary')
    def test_validate_payload_route_campaign_not_found(self, mock_summary, client):
        """Test payload validation returns 404 for missing campaign."""
        mock_summary.return_value = None
        
        response = client.get('/buyer/campaign/999/payload/validate')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['valid'] is False
        assert 'Campaign not found' in data['errors']
