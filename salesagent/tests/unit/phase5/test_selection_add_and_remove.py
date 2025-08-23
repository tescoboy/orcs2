"""Test selection add and remove functionality."""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from api.buyer_ui_router import buyer_ui_bp


class TestSelectionAddAndRemove:
    """Test selection add and remove functionality."""
    
    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        app.register_blueprint(buyer_ui_bp)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    @patch('api.buyer_ui_router.add_to_selection')
    def test_add_to_selection_success(self, mock_add, client):
        """Test POST /buyer/selection/add adds product and returns count."""
        mock_add.return_value = True
        
        response = client.post('/buyer/selection/add', data={
            'product_key': 'pub1:prod1',
            'product_id': 'prod1',
            'product_name': 'Test Product',
            'publisher_name': 'Test Publisher',
            'publisher_tenant_id': 'pub1',
            'price_cpm': '5.50',
            'delivery_type': 'guaranteed',
            'image_url': 'https://example.com/image.jpg',
            'rationale': 'Perfect match'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'count' in data
        
        mock_add.assert_called_once()
        call_args = mock_add.call_args
        assert call_args[0][1] == 'pub1:prod1'  # session_id, product_key
    
    @patch('api.buyer_ui_router.add_to_selection')
    def test_add_to_selection_failure(self, mock_add, client):
        """Test add to selection returns error on failure."""
        mock_add.return_value = False
        
        response = client.post('/buyer/selection/add', data={
            'product_key': 'pub1:prod1',
            'product_id': 'prod1',
            'product_name': 'Test Product',
            'publisher_name': 'Test Publisher',
            'publisher_tenant_id': 'pub1',
            'price_cpm': '5.50',
            'delivery_type': 'guaranteed'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    @patch('api.buyer_ui_router.remove_from_selection')
    def test_remove_from_selection_success(self, mock_remove, client):
        """Test POST /buyer/selection/remove removes product and returns count."""
        mock_remove.return_value = True
        
        response = client.post('/buyer/selection/remove', data={
            'product_key': 'pub1:prod1'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'count' in data
        
        mock_remove.assert_called_once()
        call_args = mock_remove.call_args
        assert call_args[0][1] == 'pub1:prod1'  # session_id, product_key
    
    @patch('api.buyer_ui_router.remove_from_selection')
    def test_remove_from_selection_failure(self, mock_remove, client):
        """Test remove from selection returns error on failure."""
        mock_remove.return_value = False
        
        response = client.post('/buyer/selection/remove', data={
            'product_key': 'pub1:prod1'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    @patch('api.buyer_ui_router.list_selection')
    @patch('api.buyer_ui_router.get_selection_count')
    def test_get_selection_drawer(self, mock_count, mock_list, client):
        """Test GET /buyer/selection returns selection drawer."""
        mock_list.return_value = [
            {
                'id': 'prod1',
                'name': 'Test Product 1',
                'publisher_name': 'Test Publisher',
                'publisher_tenant_id': 'pub1',
                'price_cpm': 5.50,
                'delivery_type': 'guaranteed',
                'image_url': 'https://example.com/image.jpg',
                'rationale': 'Perfect match'
            },
            {
                'id': 'prod2',
                'name': 'Test Product 2',
                'publisher_name': 'Another Publisher',
                'publisher_tenant_id': 'pub2',
                'price_cpm': 12.00,
                'delivery_type': 'non_guaranteed',
                'image_url': None,
                'rationale': 'Great match'
            }
        ]
        mock_count.return_value = 2
        
        response = client.get('/buyer/selection')
        
        assert response.status_code == 200
        assert b'Test Product 1' in response.data
        assert b'Test Product 2' in response.data
        assert b'Test Publisher' in response.data
        assert b'Another Publisher' in response.data
        assert b'$5.50' in response.data
        assert b'$12.00' in response.data
        assert b'2 products selected' in response.data
        assert b'Continue to Campaign Builder' in response.data
    
    @patch('api.buyer_ui_router.clear_selection')
    def test_clear_selection_success(self, mock_clear, client):
        """Test POST /buyer/selection/clear clears all products."""
        mock_clear.return_value = True
        
        response = client.post('/buyer/selection/clear')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 0
        
        mock_clear.assert_called_once()
    
    @patch('api.buyer_ui_router.clear_selection')
    def test_clear_selection_failure(self, mock_clear, client):
        """Test clear selection returns error on failure."""
        mock_clear.return_value = False
        
        response = client.post('/buyer/selection/clear')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
