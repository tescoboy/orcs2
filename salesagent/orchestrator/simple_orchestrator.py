"""Simple orchestrator service using direct SQLite access."""

import sqlite3
import json
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SimpleOrchestratorService:
    """Simple orchestrator service using direct SQLite access."""
    
    def __init__(self, db_path="./adcp.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"SimpleOrchestratorService initialized with db_path: {self.db_path}")
    
    async def orchestrate(self, request) -> Dict[str, Any]:
        """Orchestrate product discovery across all active tenants."""
        try:
            # Get products from all active tenants
            products = self._get_products_from_all_tenants(
                max_results=request.max_results,
                include_tenant_ids=request.include_tenant_ids,
                exclude_tenant_ids=request.exclude_tenant_ids
            )
            
            # Filter and score products based on the prompt
            scored_products = await self._score_products(products, request.prompt)
            
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
            class OrchestratorResponse:
                def __init__(self, products, total, took_ms, agents, errors):
                    self.products = products
                    self.total = total
                    self.took_ms = took_ms
                    self.agents = agents
                    self.errors = errors
            
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
        """Get products from all active tenants using direct SQLite."""
        products = []
        
        try:
            self.logger.info(f"Connecting to database at: {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Debug: Check if tenants table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tenants'")
            if not cursor.fetchone():
                self.logger.error("Tenants table does not exist")
                return []
            
            # Debug: Check if products table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
            if not cursor.fetchone():
                self.logger.error("Products table does not exist")
                return []
            
            # Debug: Count products
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            self.logger.info(f"Total products in database: {product_count}")
            
            # Get active tenants
            tenant_query = "SELECT tenant_id, name FROM tenants WHERE is_active = 1"
            tenant_params = []
            
            if include_tenant_ids:
                placeholders = ','.join(['?' for _ in include_tenant_ids])
                tenant_query += f" AND tenant_id IN ({placeholders})"
                tenant_params.extend(include_tenant_ids)
            if exclude_tenant_ids:
                placeholders = ','.join(['?' for _ in exclude_tenant_ids])
                tenant_query += f" AND tenant_id NOT IN ({placeholders})"
                tenant_params.extend(exclude_tenant_ids)
            
            cursor.execute(tenant_query, tenant_params)
            tenants = cursor.fetchall()
            self.logger.info(f"Found {len(tenants)} tenants")
            
            # Get products from each tenant
            for tenant_id, tenant_name in tenants:
                product_query = """
                    SELECT product_id, name, description, formats, targeting_template, 
                           cpm, delivery_type, countries, implementation_config
                    FROM products 
                    WHERE tenant_id = ?
                    LIMIT ?
                """
                limit = max_results // len(tenants) if tenants else max_results
                cursor.execute(product_query, (tenant_id, limit))
                tenant_products = cursor.fetchall()
                self.logger.info(f"Found {len(tenant_products)} products for tenant {tenant_id}")
                
                for product_row in tenant_products:
                    (product_id, name, description, formats_json, targeting_json, 
                     cpm, delivery_type, countries_json, implementation_config_json) = product_row
                    
                    # Parse JSON fields
                    formats_raw = json.loads(formats_json) if formats_json else []
                    targeting = json.loads(targeting_json) if targeting_json else {}
                    countries = json.loads(countries_json) if countries_json else []
                    implementation_config = json.loads(implementation_config_json) if implementation_config_json else {}
                    
                    # Extract format names from the complex format objects
                    formats = []
                    if formats_raw:
                        for format_obj in formats_raw:
                            if isinstance(format_obj, dict):
                                format_name = format_obj.get('name', format_obj.get('format_id', 'Unknown'))
                                formats.append(format_name)
                            else:
                                formats.append(str(format_obj))
                    
                    product_dict = {
                        'id': str(product_id),
                        'name': name,
                        'description': description or '',
                        'image_url': None,  # No image_url in this schema
                        'publisher_name': tenant_name,
                        'publisher_tenant_id': tenant_id,
                        'formats': formats,
                        'targeting': targeting,
                        'price_cpm': float(cpm) if cpm else 0.0,
                        'delivery_type': delivery_type or 'non_guaranteed',
                        'categories': countries,  # Use countries as categories
                        'metadata': implementation_config,
                        'source_agent_id': 'local-db',
                        'score': 0.8,  # Default score
                        'rationale': f'Product from {tenant_name}',
                        'latency_ms': 50
                    }
                    products.append(product_dict)
                    
                    # Log the first few products to see what we're getting from DB
                    if len(products) <= 3:
                        self.logger.info(f"DB Product: {name} from {tenant_name}")
                        self.logger.info(f"  - Raw DB data: id={product_id}, cpm={cpm}, delivery={delivery_type}")
                        self.logger.info(f"  - Parsed formats: {formats}")
                        self.logger.info(f"  - Parsed countries: {countries}")
            
            conn.close()
            self.logger.info(f"Found {len(products)} products from {len(tenants)} tenants")
            return products
                
        except Exception as e:
            self.logger.error(f"Error getting products from tenants: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    async def _score_products(self, products: List[Dict[str, Any]], prompt: str) -> List[Dict[str, Any]]:
        """Score products using the ADK sales agent which calls Gemini."""
        try:
            # Import the ADK agent
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from src.adk.adcp_agent.agent import root_agent
            
            # Convert products to the format expected by the agent
            agent_products = []
            for product in products:
                agent_products.append({
                    'id': product['id'],
                    'name': product['name'],
                    'description': product['description'],
                    'formats': product['formats'],
                    'price_cpm': product['price_cpm'],
                    'delivery_type': product['delivery_type'],
                    'publisher_name': product['publisher_name'],
                    'targeting': product.get('targeting', {}),
                    'categories': product.get('categories', [])
                })
            
            # Create a mock context for the agent
            context = {
                'products': agent_products,
                'prompt': prompt,
                'max_results': len(products)
            }
            
            # Call the ADK agent to use its tools and Gemini-powered capabilities
            import asyncio
            
            # Create a prompt for the agent to analyze products
            agent_prompt = f"""
Please analyze and rank the following products based on this campaign brief: "{prompt}"

Available products: {json.dumps(agent_products, indent=2)}

Use your expertise as a sales agent to:
1. Analyze each product's relevance to the campaign brief
2. Consider targeting capabilities, format compatibility, and pricing
3. Rank products from most to least relevant
4. Provide detailed reasoning for your rankings

Return your analysis in JSON format with product_id, relevance_score, and reasoning for each product.
"""
            
            # Call the ADK agent (this will use the agent's Gemini model and tools)
            agent_response = await root_agent.run_async(agent_prompt)
            
            # Parse the agent's response and apply rankings
            ranked_products = self._parse_agent_rankings(products, agent_response)
            
            self.logger.info(f"Sales agent ranking completed for {len(ranked_products)} products")
            return ranked_products
            
        except Exception as e:
            self.logger.error(f"Error in sales agent ranking, falling back to keyword matching: {e}")
            # Fallback to keyword matching if agent fails
            return self._fallback_keyword_scoring(products, prompt)
    
    def _parse_agent_rankings(self, products: List[Dict[str, Any]], agent_response: str) -> List[Dict[str, Any]]:
        """Parse the sales agent's response and apply rankings to products."""
        try:
            # The agent should return a JSON response with ranked products
            import json
            
            # Try to extract JSON from the agent response
            if isinstance(agent_response, str):
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', agent_response, re.DOTALL)
                if json_match:
                    rankings_data = json.loads(json_match.group())
                else:
                    # If no JSON found, create simple rankings based on response
                    rankings_data = {"products": []}
            else:
                rankings_data = agent_response
            
            # Apply rankings
            ranking_lookup = {}
            for ranking in rankings_data.get("products", []):
                product_id = ranking.get("product_id")
                if product_id:
                    ranking_lookup[product_id] = ranking
            
            # Update products with rankings
            for i, product in enumerate(products):
                product_id = product.get("id")
                if product_id in ranking_lookup:
                    ranking = ranking_lookup[product_id]
                    product['score'] = ranking.get("relevance_score", 0.8)
                    product['rationale'] = ranking.get("reasoning", f"Ranked by sales agent")
                else:
                    # Default ranking for products not explicitly ranked
                    product['score'] = 0.5 - (i * 0.01)
                    product['rationale'] = "Default ranking from sales agent"
            
            # Sort by score descending
            products.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error parsing agent rankings: {e}")
            # Return products with default scores
            for i, product in enumerate(products):
                product['score'] = 0.8 - (i * 0.01)
                product['rationale'] = "Default ranking due to parsing error"
            return products
    
    def _fallback_keyword_scoring(self, products: List[Dict[str, Any]], prompt: str) -> List[Dict[str, Any]]:
        """Fallback keyword-based scoring when AI is not available."""
        prompt_lower = prompt.lower()
        prompt_words = set(prompt_lower.split())
        
        for product in products:
            score = 0.5  # Base score
            reasons = []
            
            # Simple keyword matching (original logic)
            if any(word in product['name'].lower() for word in prompt_words):
                score += 0.2
                reasons.append("Name matches keywords")
            
            if any(word in product['description'].lower() for word in prompt_words):
                score += 0.1
                reasons.append("Description matches keywords")
            
            product['score'] = min(score, 1.0)
            product['rationale'] = f"Keyword match: {'; '.join(reasons)}. Score: {score:.2f}"
        
        return products
