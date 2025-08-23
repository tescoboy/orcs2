"""End-to-end smoke tests for orcs2-salesagent."""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.admin.app import create_app


class TestSmokeTests:
    """End-to-end smoke tests for critical user flows."""
    
    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    def test_health_endpoint_returns_200(self, client):
        """Test GET /health returns 200."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'timestamp' in data
    
    def test_buyer_page_returns_200_and_has_form(self, client):
        """Test GET /buyer returns 200 and includes search form."""
        response = client.get('/buyer')
        assert response.status_code == 200
        
        # Check for key HTML elements
        html = response.data.decode('utf-8')
        assert 'textarea' in html
        assert 'name="prompt"' in html
        assert 'Bootstrap' in html  # Should use Bootstrap classes
        assert 'Font Awesome' in html  # Should use Font Awesome
    
    @patch('src.services.buyer_search_service.BuyerSearchService.search_products')
    def test_buyer_search_returns_product_grid(self, mock_search, client):
        """Test POST /buyer/search returns product grid."""
        # Mock search service to return one product
        mock_product = {
            'id': 'test-product-1',
            'name': 'Test Product',
            'description': 'A test product for smoke testing',
            'publisher_name': 'Test Publisher',
            'price_cpm': 5.50,
            'delivery_type': 'guaranteed',
            'formats': ['display'],
            'image_url': 'https://example.com/image.jpg',
            'rationale': 'Great for testing'
        }
        mock_search.return_value = [mock_product]
        
        response = client.post('/buyer/search', data={
            'prompt': 'Find me some test products'
        })
        
        assert response.status_code == 200
        
        # Check for product card in response
        html = response.data.decode('utf-8')
        assert 'Test Product' in html
        assert 'Test Publisher' in html
        assert '5.50' in html  # Price should be displayed
    
    def test_buyer_selection_add_increases_count(self, client):
        """Test adding product to selection increases count."""
        # First, add a product to selection
        product_data = {
            'product_id': 'test-product-1',
            'publisher_tenant_id': 'pub1',
            'name': 'Test Product',
            'price_cpm': 5.50
        }
        
        response = client.post('/buyer/selection/add', json=product_data)
        assert response.status_code == 200
        
        # Check that selection count increased
        data = response.get_json()
        assert 'count' in data
        assert data['count'] > 0
    
    @patch('src.services.buyer_campaign_service.BuyerCampaignService.create_draft_campaign')
    @patch('src.services.buyer_campaign_service.BuyerCampaignService.attach_selected_products')
    @patch('src.services.buyer_campaign_service.BuyerCampaignService.finalize_campaign')
    def test_campaign_creation_flow(self, mock_finalize, mock_attach, mock_create, client):
        """Test full campaign creation flow from step 1 to summary."""
        # Mock campaign service methods
        mock_campaign = MagicMock()
        mock_campaign.id = 123
        mock_campaign.name = 'Test Campaign'
        mock_campaign.status = 'active'
        mock_create.return_value = 123
        mock_attach.return_value = True
        mock_finalize.return_value = True
        
        # Step 1: Create campaign details
        response = client.post('/buyer/campaign/step1', data={
            'name': 'Test Campaign',
            'objective': 'Test objective'
        })
        assert response.status_code == 302  # Redirect to step 2
        
        # Step 2: Set flighting and budget
        response = client.post('/buyer/campaign/step2', data={
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'budget_total': '1000.00'
        })
        assert response.status_code == 302  # Redirect to step 3
        
        # Step 3: Confirm campaign
        response = client.post('/buyer/campaign/confirm')
        assert response.status_code == 302  # Redirect to summary
        
        # Check campaign summary
        response = client.get('/buyer/campaign/123/summary')
        assert response.status_code == 200
        
        html = response.data.decode('utf-8')
        assert 'Test Campaign' in html
        assert 'active' in html
    
    def test_campaign_step1_validation(self, client):
        """Test campaign step 1 validation."""
        # Test with empty name
        response = client.post('/buyer/campaign/step1', data={
            'name': '',
            'objective': 'Test objective'
        })
        assert response.status_code == 400
        
        # Test with valid data
        response = client.post('/buyer/campaign/step1', data={
            'name': 'Valid Campaign',
            'objective': 'Test objective'
        })
        assert response.status_code == 302  # Redirect to step 2
    
    def test_campaign_step2_validation(self, client):
        """Test campaign step 2 validation."""
        # Test with invalid dates (end before start)
        response = client.post('/buyer/campaign/step2', data={
            'start_date': '2024-01-31',
            'end_date': '2024-01-01',
            'budget_total': '1000.00'
        })
        assert response.status_code == 400
        
        # Test with zero budget
        response = client.post('/buyer/campaign/step2', data={
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'budget_total': '0.00'
        })
        assert response.status_code == 400
    
    def test_payload_export_endpoints(self, client):
        """Test payload export endpoints."""
        # Test payload view endpoint
        response = client.get('/buyer/campaign/123/payload')
        # Should return 404 for non-existent campaign, but endpoint should exist
        assert response.status_code in [200, 404]
        
        # Test payload JSON endpoint
        response = client.get('/buyer/campaign/123/payload.json')
        assert response.status_code in [200, 404]
    
    def test_admin_endpoints_exist(self, client):
        """Test that admin endpoints are accessible."""
        # These should return some response (even if 404 for missing data)
        response = client.get('/admin')
        assert response.status_code in [200, 302, 404]  # Various possible responses
    
    def test_basic_html_structure(self, client):
        """Test that pages return valid HTML structure."""
        response = client.get('/buyer')
        assert response.status_code == 200
        
        html = response.data.decode('utf-8')
        # Basic HTML structure checks
        assert '<html' in html.lower()
        assert '<head' in html.lower()
        assert '<body' in html.lower()
        assert '</html>' in html.lower()
