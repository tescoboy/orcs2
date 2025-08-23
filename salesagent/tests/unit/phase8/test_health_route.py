"""Test health route functionality."""

import pytest
from flask import Flask
from api.health_router import health_bp


class TestHealthRoute:
    """Test health check endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        app.register_blueprint(health_bp)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    def test_health_check_returns_200_and_ok_status(self, client):
        """Test GET /health returns 200 and correct JSON."""
        response = client.get('/health')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'timestamp' in data
        assert data['service'] == 'orcs2-salesagent'
    
    def test_detailed_health_check_returns_component_status(self, client):
        """Test GET /health/detailed returns component status."""
        response = client.get('/health/detailed')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'service' in data
        assert 'checks' in data
        
        checks = data['checks']
        assert 'database' in checks
        assert 'orchestrator' in checks
        assert 'buyer_ui' in checks
        assert 'campaign_builder' in checks
        
        # All checks should be 'ok' in test environment
        for check_status in checks.values():
            assert check_status == 'ok'
    
    def test_readiness_check_returns_ready_status(self, client):
        """Test GET /health/ready returns ready status."""
        response = client.get('/health/ready')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert data['status'] == 'ready'
        assert 'timestamp' in data
        assert data['service'] == 'orcs2-salesagent'
    
    def test_liveness_check_returns_alive_status(self, client):
        """Test GET /health/live returns alive status."""
        response = client.get('/health/live')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert data['status'] == 'alive'
        assert 'timestamp' in data
        assert data['service'] == 'orcs2-salesagent'
    
    def test_health_endpoints_return_valid_json(self, client):
        """Test all health endpoints return valid JSON structure."""
        endpoints = ['/health', '/health/detailed', '/health/ready', '/health/live']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert response.content_type == 'application/json'
            
            data = response.get_json()
            assert isinstance(data, dict)
            assert 'status' in data
            assert 'timestamp' in data
            assert 'service' in data
            assert data['service'] == 'orcs2-salesagent'
    
    def test_health_timestamp_format(self, client):
        """Test that timestamp is in ISO format."""
        response = client.get('/health')
        data = response.get_json()
        
        timestamp = data['timestamp']
        # Should be ISO format: YYYY-MM-DDTHH:MM:SS.microseconds
        assert 'T' in timestamp
        assert timestamp.count('-') >= 2
        assert timestamp.count(':') >= 2
