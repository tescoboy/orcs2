"""Orchestrator service for cross-tenant product discovery."""

import os
from typing import List, Dict, Any, Optional
import logging
from decimal import Decimal

from src.core.database.database_session import get_db_session
from src.core.database.models import Product, Tenant

logger = logging.getLogger(__name__)


class OrchestratorService:
    """Service for orchestrating product discovery across tenants."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def orchestrate(self, request) -> Dict[str, Any]:
        """Orchestrate product discovery across all active tenants."""
        try:
            # Get products from all active tenants
            products = self._get_products_from_all_tenants(
                max_results=request.max_results,
                include_tenant_ids=request.include_tenant_ids,
                exclude_tenant_ids=request.exclude_tenant_ids
            )
            
            # Filter and score products based on the prompt
            scored_products = self._score_products(products, request.prompt)
            
            # Sort by score and limit results
            scored_products.sort(key=lambda x: x.get('score', 0), reverse=True)
            final_products = scored_products[:request.max_results]
            
            # Create a response object that matches the expected format
            class OrchestratorResponse:
                def __init__(self, products, total, took_ms, agents, errors):
                    self.products = products
                    self.total = total
                    self.took_ms = took_ms
                    self.agents = agents
                    self.errors = errors
            
            return OrchestratorResponse(
                products=final_products,
                total=len(final_products),
                took_ms=100,  # Mock latency
                agents=[
                    {
                        'agent_id': 'local-db',
                        'publisher_tenant_id': 'all',
                        'status': 'ok',
                        'latency_ms': 100,
                        'returned': len(final_products),
                        'error_message': None
                    }
                ],
                errors=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error in orchestration: {e}")
            return OrchestratorResponse(
                products=[],
                total=0,
                took_ms=0,
                agents=[],
                errors=[str(e)]
            )
    
    def _get_products_from_all_tenants(self, max_results: int, 
                                     include_tenant_ids: Optional[List[str]] = None,
                                     exclude_tenant_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get products from all active tenants."""
        products = []
        
        # Set the database URL to the correct one
        os.environ['DATABASE_URL'] = 'sqlite:////Users/harvingupta/.adcp/adcp.db'
        
        try:
            with get_db_session() as session:
                # Get active tenants
                tenant_query = session.query(Tenant).filter(Tenant.is_active == True)
                
                if include_tenant_ids:
                    tenant_query = tenant_query.filter(Tenant.tenant_id.in_(include_tenant_ids))
                
                if exclude_tenant_ids:
                    tenant_query = tenant_query.filter(~Tenant.tenant_id.in_(exclude_tenant_ids))
                
                tenants = tenant_query.all()
                
                # Get products from each tenant
                for tenant in tenants:
                    tenant_products = session.query(Product).filter(
                        Product.tenant_id == tenant.tenant_id
                    ).limit(max_results // len(tenants) if tenants else max_results).all()
                    
                    for product in tenant_products:
                        product_dict = {
                            'id': str(product.id),
                            'name': product.name,
                            'description': product.description or '',
                            'image_url': product.image_url,
                            'publisher_name': tenant.name,
                            'publisher_tenant_id': tenant.tenant_id,
                            'formats': product.formats or [],
                            'targeting': product.targeting or {},
                            'price_cpm': float(product.price_cpm) if product.price_cpm else 0.0,
                            'delivery_type': product.delivery_type or 'non_guaranteed',
                            'categories': product.categories or [],
                            'metadata': product.metadata or {},
                            'source_agent_id': 'local-db',
                            'score': 0.8,  # Default score
                            'rationale': f'Product from {tenant.name}',
                            'latency_ms': 50
                        }
                        products.append(product_dict)
                
                self.logger.info(f"Found {len(products)} products from {len(tenants)} tenants")
                return products
                
        except Exception as e:
            self.logger.error(f"Error getting products from tenants: {e}")
            return []
    
    def _score_products(self, products: List[Dict[str, Any]], prompt: str) -> List[Dict[str, Any]]:
        """Score products based on the search prompt."""
        # Simple scoring based on prompt keywords
        prompt_lower = prompt.lower()
        
        for product in products:
            score = 0.5  # Base score
            
            # Score based on name match
            if any(word in product['name'].lower() for word in prompt_lower.split()):
                score += 0.2
            
            # Score based on description match
            if any(word in product['description'].lower() for word in prompt_lower.split()):
                score += 0.15
            
            # Score based on categories
            if any(word in ' '.join(product['categories']).lower() for word in prompt_lower.split()):
                score += 0.1
            
            # Score based on delivery type
            if 'guaranteed' in prompt_lower and product['delivery_type'] == 'guaranteed':
                score += 0.05
            
            product['score'] = min(score, 1.0)
            product['rationale'] = f"Scored {score:.2f} based on prompt relevance"
        
        return products
