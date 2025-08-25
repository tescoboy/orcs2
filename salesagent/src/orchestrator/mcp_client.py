"""
MCP (Model Context Protocol) Client for 3rd party agent communication
"""
import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC

import httpx

from src.core.schemas.agent import AgentSelectRequest, AgentStatus

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for communicating with MCP-compliant agent endpoints"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    async def call_mcp_agent(
        self,
        endpoint_url: str,
        request: AgentSelectRequest,
        agent_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an MCP-compliant agent endpoint
        
        Args:
            endpoint_url: The MCP endpoint URL
            request: The product selection request
            agent_config: Agent-specific configuration
            
        Returns:
            Dict containing products and metadata
        """
        start_time = time.time()
        
        try:
            # Prepare MCP request
            mcp_request = self._build_mcp_request(request, agent_config)
            
            # Make HTTP request to MCP endpoint
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint_url,
                    json=mcp_request,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    mcp_response = response.json()
                    return self._parse_mcp_response(mcp_response, start_time)
                else:
                    error_msg = f"MCP endpoint returned {response.status_code}: {response.text}"
                    logger.error(f"MCP call failed: {error_msg}")
                    return self._create_error_response(error_msg, start_time)
                    
        except asyncio.TimeoutError:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"MCP call timed out after {execution_time_ms}ms"
            logger.warning(error_msg)
            return self._create_error_response(error_msg, start_time)
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"MCP call failed after {execution_time_ms}ms: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(error_msg, start_time)
    
    def _build_mcp_request(self, request: AgentSelectRequest, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build MCP-compliant request
        """
        # Standard MCP request format
        mcp_request = {
            "jsonrpc": "2.0",
            "id": f"mcp_{int(time.time())}",
            "method": "tools/call",
            "params": {
                "name": "select_products",
                "arguments": {
                    "prompt": request.prompt,
                    "max_results": request.max_results,
                    "filters": request.filters or {},
                    "locale": request.locale,
                    "currency": request.currency,
                    "timeout_seconds": request.timeout_seconds
                }
            }
        }
        
        # Add agent-specific configuration if provided
        if agent_config:
            mcp_request["params"]["arguments"]["agent_config"] = agent_config
        
        return mcp_request
    
    def _parse_mcp_response(self, mcp_response: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """
        Parse MCP response and convert to standard format
        """
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        try:
            # Check for MCP error
            if "error" in mcp_response:
                error_msg = f"MCP error: {mcp_response['error'].get('message', 'Unknown error')}"
                return self._create_error_response(error_msg, start_time)
            
            # Extract result from MCP response
            result = mcp_response.get("result", {})
            
            # Parse products from MCP format
            products = self._parse_mcp_products(result.get("products", []))
            
            return {
                "products": products,
                "total_found": len(products),
                "execution_time_ms": execution_time_ms,
                "status": "active",
                "error_message": None,
                "mcp_metadata": {
                    "response_id": mcp_response.get("id"),
                    "mcp_version": mcp_response.get("jsonrpc")
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to parse MCP response: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(error_msg, start_time)
    
    def _parse_mcp_products(self, mcp_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse products from MCP format to standard format
        """
        products = []
        
        for mcp_product in mcp_products:
            try:
                # Convert MCP product to standard format
                product = {
                    "product_id": str(mcp_product.get("id", "")),
                    "name": str(mcp_product.get("name", "Unknown Product")),
                    "description": str(mcp_product.get("description", "")),
                    "price_cpm": float(mcp_product.get("price_cpm", 0.0)),
                    "score": float(mcp_product.get("score", 0.0)),
                    "formats": self._parse_list_field(mcp_product.get("formats", [])),
                    "categories": self._parse_list_field(mcp_product.get("categories", [])),
                    "targeting": self._parse_list_field(mcp_product.get("targeting", [])),
                    "image_url": str(mcp_product.get("image_url", "")),
                    "delivery_type": str(mcp_product.get("delivery_type", "standard")),
                    "rationale": str(mcp_product.get("rationale", "")),
                    "merchandising_blurb": str(mcp_product.get("merchandising_blurb", "")),
                    "publisher_tenant_id": str(mcp_product.get("publisher_tenant_id", "")),
                    "source_agent_id": str(mcp_product.get("source_agent_id", "")),
                    "mcp_metadata": mcp_product.get("metadata", {})
                }
                
                # Validate required fields
                if product["product_id"] and product["name"]:
                    products.append(product)
                else:
                    logger.warning(f"Skipping MCP product with missing required fields: {mcp_product}")
                    
            except Exception as e:
                logger.warning(f"Failed to parse MCP product: {e}")
                continue
        
        return products
    
    def _parse_list_field(self, value: Any) -> List[str]:
        """
        Parse a field that should be a list of strings
        """
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        elif isinstance(value, list):
            return [str(item).strip() for item in value if item]
        else:
            return []
    
    def _create_error_response(self, error_message: str, start_time: float) -> Dict[str, Any]:
        """
        Create error response
        """
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "products": [],
            "total_found": 0,
            "execution_time_ms": execution_time_ms,
            "status": "error",
            "error_message": error_message,
            "mcp_metadata": {}
        }
    
    async def test_mcp_endpoint(self, endpoint_url: str) -> Dict[str, Any]:
        """
        Test MCP endpoint connectivity and basic functionality
        """
        start_time = time.time()
        
        try:
            # Simple health check request
            test_request = {
                "jsonrpc": "2.0",
                "id": "health_check",
                "method": "tools/list",
                "params": {}
            }
            
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    endpoint_url,
                    json=test_request,
                    headers={"Content-Type": "application/json"}
                )
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "response_time_ms": execution_time_ms,
                        "endpoint_url": endpoint_url,
                        "message": "MCP endpoint is responding correctly"
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "response_time_ms": execution_time_ms,
                        "endpoint_url": endpoint_url,
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "response_time_ms": execution_time_ms,
                "endpoint_url": endpoint_url,
                "message": f"Connection failed: {str(e)}"
            }


# Global instance
mcp_client = MCPClient()
