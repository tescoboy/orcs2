"""
Integration tests for MCP agent integration
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, UTC

from src.orchestrator.mcp_client import mcp_client
from src.core.schemas.agent import AgentSelectRequest, AgentConfig


class TestMCPIntegration:
    """Test MCP agent integration functionality"""
    
    @pytest.fixture
    def mock_mcp_agent(self):
        """Create a mock MCP agent configuration"""
        agent = Mock(spec=AgentConfig)
        agent.agent_id = "test_mcp_agent"
        agent.tenant_id = "test_tenant"
        agent.name = "Test MCP Agent"
        agent.type = "mcp"
        agent.status.value = "active"
        agent.endpoint_url = "https://mcp-agent.example.com/api"
        agent.config = {
            "api_key": "test_api_key",
            "timeout_seconds": 10,
            "mcp_version": "1.0"
        }
        return agent
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample agent request"""
        return AgentSelectRequest(
            prompt="Find technology products for mobile advertising",
            max_results=5,
            filters={"category": "technology", "format": "mobile"},
            locale="en-US",
            currency="USD",
            timeout_seconds=10
        )
    
    @patch('httpx.AsyncClient.post')
    async def test_mcp_agent_call_success(self, mock_post, mock_mcp_agent, sample_request):
        """Test successful MCP agent call"""
        # Mock successful MCP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "mcp_123",
            "result": {
                "products": [
                    {
                        "id": "prod_1",
                        "name": "Mobile Display Banner",
                        "description": "High-performance mobile display banner",
                        "price_cpm": 8.50,
                        "score": 0.95,
                        "formats": ["display", "banner"],
                        "categories": ["technology", "mobile"],
                        "targeting": ["US", "CA"],
                        "image_url": "https://example.com/banner.jpg",
                        "delivery_type": "standard",
                        "publisher_tenant_id": "mcp_publisher",
                        "source_agent_id": "test_mcp_agent",
                        "rationale": "Perfect match for mobile technology campaigns",
                        "merchandising_blurb": "Premium mobile placement"
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        # Call MCP agent
        result = await mcp_client.call_mcp_agent(
            endpoint_url=mock_mcp_agent.endpoint_url,
            request=sample_request,
            agent_config=mock_mcp_agent.config
        )
        
        # Verify result
        assert result["status"] == "active"
        assert result["total_found"] == 1
        assert len(result["products"]) == 1
        
        product = result["products"][0]
        assert product["product_id"] == "prod_1"
        assert product["name"] == "Mobile Display Banner"
        assert product["publisher_tenant_id"] == "mcp_publisher"
        assert product["source_agent_id"] == "test_mcp_agent"
        assert product["score"] == 0.95
        assert product["price_cpm"] == 8.50
        
        # Verify MCP metadata
        assert "mcp_metadata" in result
        assert result["mcp_metadata"]["response_id"] == "mcp_123"
        assert result["mcp_metadata"]["mcp_version"] == "2.0"
        
        # Verify HTTP call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://mcp-agent.example.com/api"
        
        # Verify request payload
        request_payload = call_args[1]["json"]
        assert request_payload["jsonrpc"] == "2.0"
        assert request_payload["method"] == "tools/call"
        assert request_payload["params"]["name"] == "select_products"
        assert request_payload["params"]["arguments"]["prompt"] == sample_request.prompt
        assert request_payload["params"]["arguments"]["max_results"] == sample_request.max_results
    
    @patch('httpx.AsyncClient.post')
    async def test_mcp_agent_call_error(self, mock_post, mock_mcp_agent, sample_request):
        """Test MCP agent call with error response"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response
        
        # Call MCP agent
        result = await mcp_client.call_mcp_agent(
            endpoint_url=mock_mcp_agent.endpoint_url,
            request=sample_request,
            agent_config=mock_mcp_agent.config
        )
        
        # Verify error result
        assert result["status"] == "error"
        assert result["total_found"] == 0
        assert len(result["products"]) == 0
        assert "Internal server error" in result["error_message"]
    
    @patch('httpx.AsyncClient.post')
    async def test_mcp_agent_call_timeout(self, mock_post, mock_mcp_agent, sample_request):
        """Test MCP agent call timeout"""
        # Mock timeout
        mock_post.side_effect = asyncio.TimeoutError()
        
        # Call MCP agent
        result = await mcp_client.call_mcp_agent(
            endpoint_url=mock_mcp_agent.endpoint_url,
            request=sample_request,
            agent_config=mock_mcp_agent.config
        )
        
        # Verify timeout result
        assert result["status"] == "error"
        assert result["total_found"] == 0
        assert len(result["products"]) == 0
        assert "timeout" in result["error_message"].lower()
    
    @patch('httpx.AsyncClient.post')
    async def test_mcp_agent_call_mcp_error(self, mock_post, mock_mcp_agent, sample_request):
        """Test MCP agent call with MCP protocol error"""
        # Mock MCP error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "mcp_123",
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }
        mock_post.return_value = mock_response
        
        # Call MCP agent
        result = await mcp_client.call_mcp_agent(
            endpoint_url=mock_mcp_agent.endpoint_url,
            request=sample_request,
            agent_config=mock_mcp_agent.config
        )
        
        # Verify MCP error result
        assert result["status"] == "error"
        assert result["total_found"] == 0
        assert len(result["products"]) == 0
        assert "Method not found" in result["error_message"]
    
    @patch('httpx.AsyncClient.post')
    async def test_mcp_agent_call_malformed_response(self, mock_post, mock_mcp_agent, sample_request):
        """Test MCP agent call with malformed response"""
        # Mock malformed response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "invalid": "response"
        }
        mock_post.return_value = mock_response
        
        # Call MCP agent
        result = await mcp_client.call_mcp_agent(
            endpoint_url=mock_mcp_agent.endpoint_url,
            request=sample_request,
            agent_config=mock_mcp_agent.config
        )
        
        # Verify error result
        assert result["status"] == "error"
        assert result["total_found"] == 0
        assert len(result["products"]) == 0
    
    @patch('httpx.AsyncClient.post')
    async def test_mcp_endpoint_health_check(self, mock_post):
        """Test MCP endpoint health check"""
        # Mock successful health check
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "health_check",
            "result": {
                "tools": [
                    {
                        "name": "select_products",
                        "description": "Select products based on criteria"
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        # Test health check
        result = await mcp_client.test_mcp_endpoint("https://mcp-agent.example.com/api")
        
        # Verify health check result
        assert result["status"] == "healthy"
        assert result["endpoint_url"] == "https://mcp-agent.example.com/api"
        assert "responding correctly" in result["message"]
        assert result["response_time_ms"] > 0
    
    @patch('httpx.AsyncClient.post')
    async def test_mcp_endpoint_health_check_failure(self, mock_post):
        """Test MCP endpoint health check failure"""
        # Mock failed health check
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_post.return_value = mock_response
        
        # Test health check
        result = await mcp_client.test_mcp_endpoint("https://mcp-agent.example.com/api")
        
        # Verify health check result
        assert result["status"] == "unhealthy"
        assert result["endpoint_url"] == "https://mcp-agent.example.com/api"
        assert "HTTP 404" in result["message"]
    
    def test_mcp_request_building(self, mock_mcp_agent, sample_request):
        """Test MCP request building"""
        # Build MCP request
        mcp_request = mcp_client._build_mcp_request(sample_request, mock_mcp_agent.config)
        
        # Verify request structure
        assert mcp_request["jsonrpc"] == "2.0"
        assert mcp_request["method"] == "tools/call"
        assert mcp_request["params"]["name"] == "select_products"
        
        # Verify arguments
        arguments = mcp_request["params"]["arguments"]
        assert arguments["prompt"] == sample_request.prompt
        assert arguments["max_results"] == sample_request.max_results
        assert arguments["filters"] == sample_request.filters
        assert arguments["locale"] == sample_request.locale
        assert arguments["currency"] == sample_request.currency
        assert arguments["timeout_seconds"] == sample_request.timeout_seconds
        
        # Verify agent config is included
        assert "agent_config" in arguments
        assert arguments["agent_config"] == mock_mcp_agent.config
    
    def test_mcp_product_parsing(self):
        """Test MCP product response parsing"""
        # Sample MCP products
        mcp_products = [
            {
                "id": "prod_1",
                "name": "Test Product",
                "description": "Test description",
                "price_cpm": 10.0,
                "score": 0.9,
                "formats": ["display", "banner"],
                "categories": ["technology"],
                "targeting": ["US"],
                "image_url": "https://example.com/image.jpg",
                "delivery_type": "standard",
                "publisher_tenant_id": "pub_1",
                "source_agent_id": "agent_1",
                "rationale": "Good match",
                "merchandising_blurb": "Premium placement"
            }
        ]
        
        # Parse products
        products = mcp_client._parse_mcp_products(mcp_products)
        
        # Verify parsing
        assert len(products) == 1
        product = products[0]
        
        assert product["product_id"] == "prod_1"
        assert product["name"] == "Test Product"
        assert product["description"] == "Test description"
        assert product["price_cpm"] == 10.0
        assert product["score"] == 0.9
        assert product["formats"] == ["display", "banner"]
        assert product["categories"] == ["technology"]
        assert product["targeting"] == ["US"]
        assert product["image_url"] == "https://example.com/image.jpg"
        assert product["delivery_type"] == "standard"
        assert product["publisher_tenant_id"] == "pub_1"
        assert product["source_agent_id"] == "agent_1"
        assert product["rationale"] == "Good match"
        assert product["merchandising_blurb"] == "Premium placement"
    
    def test_mcp_list_field_parsing(self):
        """Test MCP list field parsing"""
        # Test string parsing
        result = mcp_client._parse_list_field("item1,item2,item3")
        assert result == ["item1", "item2", "item3"]
        
        # Test list parsing
        result = mcp_client._parse_list_field(["item1", "item2", "item3"])
        assert result == ["item1", "item2", "item3"]
        
        # Test empty/None parsing
        result = mcp_client._parse_list_field(None)
        assert result == []
        
        result = mcp_client._parse_list_field("")
        assert result == []
        
        result = mcp_client._parse_list_field([])
        assert result == []
