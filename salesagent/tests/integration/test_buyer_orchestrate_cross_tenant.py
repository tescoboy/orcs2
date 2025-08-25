"""
Integration tests for buyer orchestrator cross-tenant functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, UTC

from src.services.orchestrator_service import orchestrator_service
from src.core.schemas.agent import AgentSelectRequest, AgentConfig, AgentStatus
from src.core.database.models import Tenant, Product


class TestBuyerOrchestrateCrossTenant:
    """Test cross-tenant orchestration functionality"""
    
    @pytest.fixture
    def mock_tenants(self):
        """Create mock tenants for testing"""
        tenants = []
        
        # Tenant 1
        tenant1 = Mock(spec=Tenant)
        tenant1.tenant_id = "tenant_1"
        tenant1.name = "Test Tenant 1"
        tenant1.config = {
            'agents': {
                'tenant_1_local_ai': {
                    'name': 'Tenant 1 Local AI',
                    'type': 'local_ai',
                    'status': 'active',
                    'endpoint_url': '/tenant/tenant_1/agent/local_ai',
                    'config': {'model': 'gemini-2.0-flash-exp'}
                }
            }
        }
        tenants.append(tenant1)
        
        # Tenant 2
        tenant2 = Mock(spec=Tenant)
        tenant2.tenant_id = "tenant_2"
        tenant2.name = "Test Tenant 2"
        tenant2.config = {
            'agents': {
                'tenant_2_local_ai': {
                    'name': 'Tenant 2 Local AI',
                    'type': 'local_ai',
                    'status': 'active',
                    'endpoint_url': '/tenant/tenant_2/agent/local_ai',
                    'config': {'model': 'gemini-2.0-flash-exp'}
                }
            }
        }
        tenants.append(tenant2)
        
        return tenants
    
    @pytest.fixture
    def mock_products(self):
        """Create mock products for testing"""
        products = []
        
        # Products for tenant 1
        for i in range(3):
            product = Mock(spec=Product)
            product.product_id = f"prod_1_{i}"
            product.name = f"Product 1-{i}"
            product.description = f"Description for product 1-{i}"
            product.price_cpm = 10.0 + i
            product.formats = "display,banner"
            product.categories = "technology,business"
            product.targeting = "US,CA"
            product.image_url = f"https://example.com/prod_1_{i}.jpg"
            product.delivery_type = "standard"
            product.tenant_id = "tenant_1"
            products.append(product)
        
        # Products for tenant 2
        for i in range(2):
            product = Mock(spec=Product)
            product.product_id = f"prod_2_{i}"
            product.name = f"Product 2-{i}"
            product.description = f"Description for product 2-{i}"
            product.price_cpm = 15.0 + i
            product.formats = "video,display"
            product.categories = "entertainment,technology"
            product.targeting = "US,UK"
            product.image_url = f"https://example.com/prod_2_{i}.jpg"
            product.delivery_type = "premium"
            product.tenant_id = "tenant_2"
            products.append(product)
        
        return products
    
    @patch('src.services.agent_management_service.agent_management_service.discover_active_agents')
    @patch('src.orchestrator.fanout.fanout_orchestrator.fanout_to_agents')
    async def test_cross_tenant_orchestration(
        self, 
        mock_fanout, 
        mock_discover_agents, 
        mock_tenants, 
        mock_products
    ):
        """Test orchestration across multiple tenants"""
        # Mock agent discovery
        mock_discover_agents.return_value = [
            (Mock(spec=AgentConfig), "tenant_1", "Test Tenant 1"),
            (Mock(spec=AgentConfig), "tenant_2", "Test Tenant 2")
        ]
        
        # Mock fanout results
        mock_fanout.return_value = (
            [
                {
                    "product_id": "prod_1_0",
                    "name": "Product 1-0",
                    "publisher_tenant_id": "tenant_1",
                    "source_agent_id": "tenant_1_local_ai",
                    "score": 0.9,
                    "price_cpm": 10.0
                },
                {
                    "product_id": "prod_2_0",
                    "name": "Product 2-0",
                    "publisher_tenant_id": "tenant_2",
                    "source_agent_id": "tenant_2_local_ai",
                    "score": 0.8,
                    "price_cpm": 15.0
                }
            ],
            []  # No agent reports for simplicity
        )
        
        # Create request
        request = AgentSelectRequest(
            prompt="Find technology products",
            max_results=10,
            filters={},
            locale="en-US",
            currency="USD",
            timeout_seconds=10
        )
        
        # Call orchestrator
        response = await orchestrator_service.orchestrate(request)
        
        # Verify response
        assert "products" in response
        assert "metadata" in response
        assert len(response["products"]) == 2
        
        # Verify products from both tenants
        tenant_ids = set(product["publisher_tenant_id"] for product in response["products"])
        assert "tenant_1" in tenant_ids
        assert "tenant_2" in tenant_ids
        
        # Verify metadata
        metadata = response["metadata"]
        assert metadata["total_agents_contacted"] == 2
        assert metadata["successful_agents"] == 2
        assert metadata["total_products_found"] == 2
    
    @patch('src.services.agent_management_service.agent_management_service.discover_active_agents')
    @patch('src.orchestrator.fanout.fanout_orchestrator.fanout_to_agents')
    async def test_tenant_filtering(
        self, 
        mock_fanout, 
        mock_discover_agents, 
        mock_tenants, 
        mock_products
    ):
        """Test filtering by specific tenants"""
        # Mock agent discovery for specific tenant
        mock_discover_agents.return_value = [
            (Mock(spec=AgentConfig), "tenant_1", "Test Tenant 1")
        ]
        
        # Mock fanout results
        mock_fanout.return_value = (
            [
                {
                    "product_id": "prod_1_0",
                    "name": "Product 1-0",
                    "publisher_tenant_id": "tenant_1",
                    "source_agent_id": "tenant_1_local_ai",
                    "score": 0.9,
                    "price_cpm": 10.0
                }
            ],
            []
        )
        
        # Create request
        request = AgentSelectRequest(
            prompt="Find technology products",
            max_results=10,
            filters={},
            locale="en-US",
            currency="USD",
            timeout_seconds=10
        )
        
        # Call orchestrator with tenant filter
        response = await orchestrator_service.orchestrate(
            request,
            include_tenant_ids=["tenant_1"]
        )
        
        # Verify only tenant_1 products
        assert len(response["products"]) == 1
        assert response["products"][0]["publisher_tenant_id"] == "tenant_1"
    
    @patch('src.services.agent_management_service.agent_management_service.discover_active_agents')
    @patch('src.orchestrator.fanout.fanout_orchestrator.fanout_to_agents')
    async def test_agent_type_filtering(
        self, 
        mock_fanout, 
        mock_discover_agents, 
        mock_tenants, 
        mock_products
    ):
        """Test filtering by agent types"""
        # Mock agent discovery for specific agent type
        mock_discover_agents.return_value = [
            (Mock(spec=AgentConfig), "tenant_1", "Test Tenant 1")
        ]
        
        # Mock fanout results
        mock_fanout.return_value = (
            [
                {
                    "product_id": "prod_1_0",
                    "name": "Product 1-0",
                    "publisher_tenant_id": "tenant_1",
                    "source_agent_id": "tenant_1_local_ai",
                    "score": 0.9,
                    "price_cpm": 10.0
                }
            ],
            []
        )
        
        # Create request
        request = AgentSelectRequest(
            prompt="Find technology products",
            max_results=10,
            filters={},
            locale="en-US",
            currency="USD",
            timeout_seconds=10
        )
        
        # Call orchestrator with agent type filter
        response = await orchestrator_service.orchestrate(
            request,
            agent_types=["local_ai"]
        )
        
        # Verify response
        assert len(response["products"]) == 1
        assert response["products"][0]["source_agent_id"] == "tenant_1_local_ai"
    
    @patch('src.services.agent_management_service.agent_management_service.discover_active_agents')
    async def test_no_agents_found(self, mock_discover_agents):
        """Test orchestration when no agents are found"""
        # Mock no agents found
        mock_discover_agents.return_value = []
        
        # Create request
        request = AgentSelectRequest(
            prompt="Find technology products",
            max_results=10,
            filters={},
            locale="en-US",
            currency="USD",
            timeout_seconds=10
        )
        
        # Call orchestrator
        response = await orchestrator_service.orchestrate(request)
        
        # Verify empty response
        assert response["products"] == []
        assert response["agent_reports"] == []
        assert response["metadata"]["total_agents_contacted"] == 0
        assert response["metadata"]["successful_agents"] == 0
    
    @patch('src.services.agent_management_service.agent_management_service.discover_active_agents')
    @patch('src.orchestrator.fanout.fanout_orchestrator.fanout_to_agents')
    async def test_partial_failure(
        self, 
        mock_fanout, 
        mock_discover_agents, 
        mock_tenants, 
        mock_products
    ):
        """Test orchestration with partial agent failures"""
        # Mock agent discovery
        mock_discover_agents.return_value = [
            (Mock(spec=AgentConfig), "tenant_1", "Test Tenant 1"),
            (Mock(spec=AgentConfig), "tenant_2", "Test Tenant 2")
        ]
        
        # Mock fanout with partial failure
        mock_fanout.return_value = (
            [
                {
                    "product_id": "prod_1_0",
                    "name": "Product 1-0",
                    "publisher_tenant_id": "tenant_1",
                    "source_agent_id": "tenant_1_local_ai",
                    "score": 0.9,
                    "price_cpm": 10.0
                }
            ],
            [
                Mock(status=AgentStatus.ACTIVE, products_count=1),
                Mock(status=AgentStatus.ERROR, products_count=0)
            ]
        )
        
        # Create request
        request = AgentSelectRequest(
            prompt="Find technology products",
            max_results=10,
            filters={},
            locale="en-US",
            currency="USD",
            timeout_seconds=10
        )
        
        # Call orchestrator
        response = await orchestrator_service.orchestrate(request)
        
        # Verify partial success
        assert len(response["products"]) == 1
        assert response["metadata"]["total_agents_contacted"] == 2
        assert response["metadata"]["successful_agents"] == 1
        assert response["metadata"]["failed_agents"] == 1


class TestBuyerOrchestrateAPI:
    """Test the buyer orchestrator API endpoints"""
    
    def test_orchestrate_endpoint_validation(self, client):
        """Test request validation in orchestrate endpoint"""
        # Test missing request body
        response = client.post('/buyer/orchestrate')
        assert response.status_code == 400
        assert "Request body is required" in response.json["error"]
        
        # Test invalid request format
        response = client.post('/buyer/orchestrate', json={"invalid": "data"})
        assert response.status_code == 400
        assert "Invalid request format" in response.json["error"]
    
    def test_orchestrate_endpoint_success(self, client):
        """Test successful orchestration request"""
        # Mock the orchestrator service
        with patch('src.api.buyer_orchestrator_router.orchestrator_service') as mock_orchestrator:
            mock_orchestrator.orchestrate.return_value = {
                "products": [],
                "agent_reports": [],
                "metadata": {
                    "total_agents_contacted": 0,
                    "successful_agents": 0,
                    "failed_agents": 0,
                    "total_products_found": 0,
                    "total_products_after_dedupe": 0,
                    "orchestration_time_ms": 100
                }
            }
            
            # Make request
            response = client.post('/buyer/orchestrate', json={
                "prompt": "Find technology products",
                "max_results": 10,
                "filters": {},
                "locale": "en-US",
                "currency": "USD",
                "timeout_seconds": 10
            })
            
            assert response.status_code == 200
            assert "products" in response.json
            assert "metadata" in response.json
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/buyer/orchestrate/health')
        assert response.status_code == 200
        assert "status" in response.json
    
    def test_agents_endpoint(self, client):
        """Test agents listing endpoint"""
        response = client.get('/buyer/orchestrate/agents')
        assert response.status_code == 200
        assert "agents" in response.json
        assert "total_agents" in response.json
    
    def test_tenants_endpoint(self, client):
        """Test tenants listing endpoint"""
        response = client.get('/buyer/orchestrate/tenants')
        assert response.status_code == 200
        assert "tenants" in response.json
        assert "total_tenants" in response.json
