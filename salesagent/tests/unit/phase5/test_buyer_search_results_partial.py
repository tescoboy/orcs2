"""Test buyer search results partial renders correctly."""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from api.buyer_ui_router import buyer_ui_bp


class TestBuyerSearchResultsPartial:
    """Test buyer search results partial renders correctly."""
    
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
    
    @patch('api.buyer_ui_router.search_products')
    def test_search_returns_product_cards(self, mock_search, client):
        """Test POST /buyer/search returns HTML with product cards."""
        # Mock search results
        mock_products = [
            {
                'id': 'test-1',
                'name': 'Test Product 1',
                'description': 'Test description 1',
                'image_url': 'https://example.com/image1.jpg',
                'publisher_name': 'Test Publisher',
                'publisher_tenant_id': 'test-pub',
                'formats': ['display', 'banner'],
                'targeting': {'geo': ['US'], 'interests': ['tech']},
                'price_cpm': 5.50,
                'delivery_type': 'guaranteed',
                'categories': ['technology'],
                'metadata': {},
                'source_agent_id': 'agent-1',
                'score': 0.95,
                'rationale': 'Perfect match for tech campaigns',
                'latency_ms': 150
            },
            {
                'id': 'test-2',
                'name': 'Test Product 2',
                'description': 'Test description 2',
                'image_url': None,
                'publisher_name': 'Another Publisher',
                'publisher_tenant_id': 'another-pub',
                'formats': ['video'],
                'targeting': {'geo': ['CA']},
                'price_cpm': 12.00,
                'delivery_type': 'non_guaranteed',
                'categories': ['entertainment'],
                'metadata': {},
                'source_agent_id': 'agent-2',
                'score': 0.88,
                'rationale': 'Great for entertainment',
                'latency_ms': 200
            }
        ]
        mock_search.return_value = mock_products
        
        response = client.post('/buyer/search', data={
            'prompt': 'Test campaign brief',
            'max_results': '10'
        })
        
        assert response.status_code == 200
        assert b'Found 2 products' in response.data
        assert b'Test Product 1' in response.data
        assert b'Test Product 2' in response.data
        assert b'Test Publisher' in response.data
        assert b'Another Publisher' in response.data
        assert b'$5.50' in response.data
        assert b'$12.00' in response.data
        assert b'guaranteed' in response.data
        assert b'non_guaranteed' in response.data
    
    @patch('api.buyer_ui_router.search_products')
    def test_search_returns_error_for_empty_prompt(self, mock_search, client):
        """Test search returns error for empty prompt."""
        response = client.post('/buyer/search', data={
            'prompt': '',
            'max_results': '10'
        })
        
        assert response.status_code == 200
        assert b'Please enter a search prompt' in response.data
        mock_search.assert_not_called()
    
    @patch('api.buyer_ui_router.search_products')
    def test_search_uses_bootstrap_classes(self, mock_search, client):
        """Test search results use Bootstrap classes and no inline CSS."""
        mock_products = [{
            'id': 'test-1',
            'name': 'Test Product',
            'description': 'Test description',
            'image_url': None,
            'publisher_name': 'Test Publisher',
            'publisher_tenant_id': 'test-pub',
            'formats': ['display'],
            'targeting': {},
            'price_cpm': 5.50,
            'delivery_type': 'guaranteed',
            'categories': [],
            'metadata': {},
            'source_agent_id': 'agent-1',
            'score': 0.95,
            'rationale': 'Perfect match',
            'latency_ms': 150
        }]
        mock_search.return_value = mock_products
        
        response = client.post('/buyer/search', data={
            'prompt': 'Test campaign',
            'max_results': '10'
        })
        
        assert response.status_code == 200
        # Check for Bootstrap classes
        assert b'row' in response.data
        assert b'col' in response.data
        assert b'card' in response.data
        assert b'badge' in response.data
        assert b'btn' in response.data
        
        # Check no inline CSS
        assert b'style="' not in response.data
    
    @patch('api.buyer_ui_router.search_products')
    def test_search_handles_filters(self, mock_search, client):
        """Test search handles include/exclude filters."""
        mock_search.return_value = []
        
        response = client.post('/buyer/search', data={
            'prompt': 'Test campaign',
            'max_results': '10',
            'include_tenant_ids': ['pub1', 'pub2'],
            'exclude_tenant_ids': ['pub3'],
            'include_agent_ids': ['agent1']
        })
        
        assert response.status_code == 200
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args[1]['include_tenant_ids'] == ['pub1', 'pub2']
        assert call_args[1]['exclude_tenant_ids'] == ['pub3']
        assert call_args[1]['include_agent_ids'] == ['agent1']
