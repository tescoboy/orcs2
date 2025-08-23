"""Test campaign Step 1 validation."""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from api.buyer_campaign_router import buyer_campaign_bp


class TestCampaignStep1Validation:
    """Test campaign Step 1 validation."""
    
    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        app.register_blueprint(buyer_campaign_bp)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    @patch('api.buyer_campaign_router.get_selection_count')
    def test_get_new_campaign_with_products(self, mock_count, client):
        """Test GET /buyer/campaign/new with products in selection."""
        mock_count.return_value = 3
        
        response = client.get('/buyer/campaign/new')
        
        assert response.status_code == 200
        assert b'Create Campaign' in response.data
        assert b'Step 1 of 3' in response.data
        assert b'3 products selected' in response.data
    
    @patch('api.buyer_campaign_router.get_selection_count')
    def test_get_new_campaign_no_products(self, mock_count, client):
        """Test GET /buyer/campaign/new with no products in selection."""
        mock_count.return_value = 0
        
        response = client.get('/buyer/campaign/new')
        
        assert response.status_code == 302  # Redirect
        assert b'Please add products' in response.data
    
    @patch('api.buyer_campaign_router.get_or_create_session_id')
    @patch('api.buyer_campaign_router.BuyerCampaignCore.validate_step1_data')
    @patch('api.buyer_campaign_router.BuyerCampaignCore.store_step1_data')
    def test_step1_submit_valid_data(self, mock_store, mock_validate, mock_session, client):
        """Test POST /buyer/campaign/step1 with valid data."""
        mock_session.return_value = 'test-session-id'
        mock_validate.return_value = True
        mock_store.return_value = None
        
        response = client.post('/buyer/campaign/step1', data={
            'name': 'Test Campaign',
            'objective': 'Test objective'
        })
        
        assert response.status_code == 302  # Redirect to step2
        mock_validate.assert_called_once_with('Test Campaign')
        mock_store.assert_called_once_with('test-session-id', 'Test Campaign', 'Test objective')
    
    @patch('api.buyer_campaign_router.get_or_create_session_id')
    @patch('api.buyer_campaign_router.BuyerCampaignCore.validate_step1_data')
    def test_step1_submit_empty_name(self, mock_validate, mock_session, client):
        """Test POST /buyer/campaign/step1 with empty name."""
        mock_session.return_value = 'test-session-id'
        mock_validate.return_value = False
        
        response = client.post('/buyer/campaign/step1', data={
            'name': '',
            'objective': 'Test objective'
        })
        
        assert response.status_code == 400
        assert b'Campaign name is required' in response.data
        mock_validate.assert_called_once_with('')
    
    @patch('api.buyer_campaign_router.get_or_create_session_id')
    @patch('api.buyer_campaign_router.BuyerCampaignCore.validate_step1_data')
    def test_step1_submit_whitespace_name(self, mock_validate, mock_session, client):
        """Test POST /buyer/campaign/step1 with whitespace name."""
        mock_session.return_value = 'test-session-id'
        mock_validate.return_value = False
        
        response = client.post('/buyer/campaign/step1', data={
            'name': '   ',
            'objective': 'Test objective'
        })
        
        assert response.status_code == 400
        assert b'Campaign name is required' in response.data
        mock_validate.assert_called_once_with('   ')
    
    def test_step1_page_uses_bootstrap_classes(self, client):
        """Test Step 1 page uses Bootstrap classes and no inline CSS."""
        with patch('api.buyer_campaign_router.get_selection_count', return_value=3):
            response = client.get('/buyer/campaign/new')
            
            assert response.status_code == 200
            # Check for Bootstrap classes
            assert b'container-fluid' in response.data
            assert b'row' in response.data
            assert b'col-12' in response.data
            assert b'card' in response.data
            assert b'btn' in response.data
            assert b'form-control' in response.data
            
            # Check no inline CSS
            assert b'style="' not in response.data
    
    def test_step1_page_contains_progress_bar(self, client):
        """Test Step 1 page contains progress bar."""
        with patch('api.buyer_campaign_router.get_selection_count', return_value=3):
            response = client.get('/buyer/campaign/new')
            
            assert response.status_code == 200
            assert b'progress' in response.data
            assert b'progress-bar' in response.data
            assert b'33%' in response.data
            assert b'Details' in response.data
            assert b'Flighting & Budget' in response.data
            assert b'Review & Confirm' in response.data
