"""Test buyer page renders correctly."""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from api.buyer_ui_router import buyer_ui_bp


class TestBuyerPageRenders:
    """Test buyer page renders correctly."""
    
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
    
    def test_get_buyer_returns_200_with_form(self, client):
        """Test GET /buyer returns 200 and contains a form with textarea."""
        response = client.get('/buyer/')
        
        assert response.status_code == 200
        assert b'<form' in response.data
        assert b'textarea' in response.data
        assert b'name="prompt"' in response.data
        assert b'Product Discovery' in response.data
    
    def test_buyer_page_contains_basket_icon(self, client):
        """Test buyer page contains basket icon with count badge."""
        response = client.get('/buyer/')
        
        assert response.status_code == 200
        assert b'fa-shopping-cart' in response.data
        assert b'selection-count' in response.data
        assert b'0' in response.data  # Initial count
    
    def test_buyer_page_uses_bootstrap_classes(self, client):
        """Test buyer page uses Bootstrap classes and no inline CSS."""
        response = client.get('/buyer/')
        
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
    
    def test_buyer_page_contains_htmx_attributes(self, client):
        """Test buyer page contains HTMX attributes for progressive enhancement."""
        response = client.get('/buyer/')
        
        assert response.status_code == 200
        assert b'hx-post' in response.data
        assert b'hx-target' in response.data
        assert b'hx-swap' in response.data
        assert b'htmx-indicator' in response.data
    
    def test_buyer_page_contains_search_form_fields(self, client):
        """Test buyer page contains all required search form fields."""
        response = client.get('/buyer/')
        
        assert response.status_code == 200
        # Check for form fields
        assert b'name="prompt"' in response.data
        assert b'name="max_results"' in response.data
        assert b'name="include_tenant_ids"' in response.data
        assert b'name="exclude_tenant_ids"' in response.data
        assert b'Campaign Brief' in response.data
        assert b'Max Results' in response.data
        assert b'Filters' in response.data
