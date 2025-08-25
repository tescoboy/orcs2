"""Buyer search service that wraps the orchestrator for product discovery."""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def search_products(prompt: str, filters: Optional[Dict[str, Any]] = None, 
                   include_tenant_ids: Optional[List[str]] = None,
                   exclude_tenant_ids: Optional[List[str]] = None,
                   include_agent_ids: Optional[List[str]] = None,
                   max_results: int = 50) -> List[Dict[str, Any]]:
    """Search for products using the orchestrator service."""
    try:
        # Set the correct database URL
        import os
        os.environ['DATABASE_URL'] = 'sqlite:///./adcp.db'
        
        # Import the simple orchestrator service directly to avoid HTTP round trips
        import sys
        import os
        # Add the salesagent directory to the path so we can import from orchestrator and schemas
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from src.services.orchestrator_service import orchestrator_service
        from src.core.schemas.agent import AgentSelectRequest
        
        # Build the request
        request_data = AgentSelectRequest(
            prompt=prompt,
            max_results=max_results,
            filters=filters or {},
            locale="en-US",
            currency="USD",
            timeout_seconds=10
        )
        
        # Call the orchestrator
        import asyncio
        response = asyncio.run(orchestrator_service.orchestrate(
            request=request_data,
            include_tenant_ids=include_tenant_ids,
            exclude_tenant_ids=exclude_tenant_ids,
            include_agent_ids=include_agent_ids
        ))
        
        # Extract products from response
        products = response.get("products", [])
        
        logger.info(f"Search returned {len(products)} products for prompt: {prompt[:50]}...")
        
        # Add detailed logging to see what products are being returned
        for i, product in enumerate(products[:3]):  # Log first 3 products
            logger.info(f"Product {i+1}: {product.get('name', 'NO_NAME')} from {product.get('publisher_name', 'NO_PUBLISHER')}")
            logger.info(f"  - Description: {product.get('description', 'NO_DESC')[:100]}...")
            logger.info(f"  - Price: ${product.get('price_cpm', 0)} CPM")
            logger.info(f"  - Delivery: {product.get('delivery_type', 'NO_TYPE')}")
            logger.info(f"  - Formats: {product.get('formats', [])}")
            logger.info(f"  - Categories: {product.get('categories', [])}")
        
        return products
        
    except ImportError as e:
        logger.error(f"Failed to import orchestrator service: {e}")
        # Return mock data for development/testing
        return _get_mock_products(prompt, max_results)
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return []


def _get_mock_products(prompt: str, max_results: int) -> List[Dict[str, Any]]:
    """Return mock products for development/testing."""
    mock_products = [
        {
            'id': 'mock-1',
            'name': 'Premium Display Banner',
            'description': 'High-impact display banner with premium placement and targeting capabilities.',
            'image_url': 'https://via.placeholder.com/300x250/007bff/ffffff?text=Display+Banner',
            'publisher_name': 'TechNews Daily',
            'publisher_tenant_id': 'technews-daily',
            'formats': ['display', 'banner'],
            'targeting': {'geo': ['US', 'CA'], 'interests': ['technology', 'business']},
            'price_cpm': 5.50,
            'delivery_type': 'guaranteed',
            'categories': ['technology', 'business'],
            'metadata': {'placement': 'above-fold', 'viewability': 'high'},
            'source_agent_id': 'agent-1',
            'score': 0.95,
            'rationale': 'Perfect match for technology-focused campaigns with premium placement.',
            'latency_ms': 150
        },
        {
            'id': 'mock-2',
            'name': 'Video Pre-roll',
            'description': 'Engaging video pre-roll with high completion rates and brand safety.',
            'image_url': 'https://via.placeholder.com/640x360/28a745/ffffff?text=Video+Pre-roll',
            'publisher_name': 'Entertainment Hub',
            'publisher_tenant_id': 'entertainment-hub',
            'formats': ['video', 'pre-roll'],
            'targeting': {'geo': ['US'], 'demographics': ['18-34']},
            'price_cpm': 12.00,
            'delivery_type': 'non_guaranteed',
            'categories': ['entertainment', 'lifestyle'],
            'metadata': {'duration': '15s', 'completion_rate': '85%'},
            'source_agent_id': 'agent-2',
            'score': 0.88,
            'rationale': 'Great for reaching young audiences with engaging video content.',
            'latency_ms': 200
        },
        {
            'id': 'mock-3',
            'name': 'Native Article',
            'description': 'Seamlessly integrated native content that matches editorial style.',
            'image_url': 'https://via.placeholder.com/400x300/ffc107/000000?text=Native+Article',
            'publisher_name': 'Lifestyle Magazine',
            'publisher_tenant_id': 'lifestyle-mag',
            'formats': ['native', 'article'],
            'targeting': {'interests': ['lifestyle', 'health', 'wellness']},
            'price_cpm': 8.25,
            'delivery_type': 'guaranteed',
            'categories': ['lifestyle', 'health'],
            'metadata': {'word_count': '800', 'engagement_rate': 'high'},
            'source_agent_id': 'agent-3',
            'score': 0.82,
            'rationale': 'Excellent for lifestyle and wellness brands with high engagement.',
            'latency_ms': 180
        }
    ]
    
    # Filter based on prompt keywords (simple mock logic)
    if 'video' in prompt.lower():
        return [p for p in mock_products if 'video' in p['formats']][:max_results]
    elif 'native' in prompt.lower():
        return [p for p in mock_products if 'native' in p['formats']][:max_results]
    else:
        return mock_products[:max_results]
