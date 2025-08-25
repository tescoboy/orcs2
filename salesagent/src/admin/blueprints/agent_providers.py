"""
Agent Provider Endpoints - Direct product selection for orchestrator
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC

from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError

from src.core.schemas.agent import AgentSelectRequest, AgentSelectResponse, AgentStatus
from src.services.agent_management_service import agent_management_service
from src.services.ai_ranking_service import select_products_for_tenant
from src.core.database.database_session import get_db_session
from src.core.database.models import Product
from src.repositories.agents_repo import AgentRepository

logger = logging.getLogger(__name__)

# Create Blueprint
agent_providers_bp = Blueprint("agent_providers", __name__, url_prefix="/tenant")


@agent_providers_bp.route("/<tenant_id>/agent/<agent_type>/select_products", methods=["POST"])
def select_products(tenant_id: str, agent_type: str):
    """
    Direct product selection endpoint for agents
    
    This endpoint is called by the orchestrator to get ranked products
    from a specific agent, bypassing the ADK chat layer.
    """
    start_time = time.time()
    
    try:
        # Validate request
        try:
            request_data = request.get_json()
            if not request_data:
                return jsonify({
                    "error": "Request body is required",
                    "status": "error"
                }), 400
            
            agent_request = AgentSelectRequest(**request_data)
        except ValidationError as e:
            return jsonify({
                "error": f"Invalid request format: {str(e)}",
                "status": "error"
            }), 400
        
        # Get agent details - look for agent with matching type in this tenant
        agent = None
        
        # Use Flask app's database session
        with get_db_session() as db_session:
            repo = AgentRepository(db_session)
            agents_data = repo.list_active_agents_across_tenants(
                include_tenant_ids=[tenant_id],
                agent_types=[agent_type]
            )
        
        logger.info(f"Looking for agent type '{agent_type}' in tenant '{tenant_id}'")
        logger.info(f"Found {len(agents_data)} agents in tenant")
        
        for found_agent, found_tenant_id, found_tenant_name in agents_data:
            logger.info(f"Checking agent: {found_agent.agent_id}, type: '{found_agent.type}', expected: '{agent_type}'")
            if found_agent.type == agent_type:
                agent = found_agent
                logger.info(f"Found matching agent: {agent.agent_id}")
                break
        
        if not agent:
            return jsonify({
                "error": f"Agent with type {agent_type} not found for tenant {tenant_id}",
                "status": "error"
            }), 404
        
        if agent.status != AgentStatus.ACTIVE:
            return jsonify({
                "error": f"Agent {agent.agent_id} is not active (status: {agent.status.value})",
                "status": "error"
            }), 400
        
        logger.info(f"Processing product selection request for agent {agent.agent_id} "
                   f"with prompt: '{agent_request.prompt[:100]}...'")
        
        # Get products from database
        with get_db_session() as db_session:
            products = db_session.query(Product).all()
            
            if not products:
                logger.warning(f"No products found for tenant {tenant_id}")
                return _create_response(
                    agent.agent_id, tenant_id, [], 0, start_time, 
                    "No products available for this tenant"
                )
        
        # Convert products to list format
        products_list = []
        for product in products:
            product_dict = {
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "price_cpm": float(product.cpm) if product.cpm else 0.0,
                "formats": product.formats if isinstance(product.formats, list) else [],
                "categories": [],  # Product model doesn't have categories field
                "targeting": product.targeting_template if isinstance(product.targeting_template, list) else [],
                "image_url": None,  # Product model doesn't have image_url field
                "delivery_type": product.delivery_type,
                "publisher_tenant_id": tenant_id,
                "source_agent_id": agent.agent_id
            }
            products_list.append(product_dict)
        
        # Use AI ranking service to score and rank products
        try:
            import asyncio
            ranked_products = asyncio.run(_rank_products_with_ai(
                agent_request.prompt, 
                products_list, 
                agent_request.max_results,
                agent.config
            ))
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return _create_response(
                agent.agent_id, tenant_id, ranked_products, len(products_list), 
                start_time, None, execution_time_ms
            )
            
        except Exception as ai_error:
            logger.error(f"AI ranking failed for agent {agent.agent_id}: {ai_error}")
            
            # Fallback to simple keyword matching
            fallback_products = _fallback_keyword_ranking(
                agent_request.prompt, 
                products_list, 
                agent_request.max_results
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return _create_response(
                agent.agent_id, tenant_id, fallback_products, len(products_list), 
                start_time, f"AI ranking failed, using fallback: {str(ai_error)}", 
                execution_time_ms
            )
    
    except Exception as e:
        logger.error(f"Error in select_products for tenant {tenant_id}, agent {agent_type}: {e}", exc_info=True)
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return jsonify({
            "agent_id": f"{tenant_id}_{agent_type}",
            "tenant_id": tenant_id,
            "products": [],
            "total_found": 0,
            "execution_time_ms": execution_time_ms,
            "status": "error",
            "error_message": str(e)
        }), 500


async def _rank_products_with_ai(
    prompt: str, 
    products: List[Dict[str, Any]], 
    max_results: int,
    agent_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Rank products using AI service
    """
    try:
        # Call the AI ranking service (not async)
        ranked_products = select_products_for_tenant(
            tenant_id=products[0]["publisher_tenant_id"] if products else None,
            prompt=prompt,
            products=products,
            max_results=max_results
        )
        
        # Add source information to each product
        for product in ranked_products:
            product["source_agent_id"] = products[0]["source_agent_id"] if products else None
            product["publisher_tenant_id"] = products[0]["publisher_tenant_id"] if products else None
        
        return ranked_products
        
    except Exception as e:
        logger.error(f"AI ranking error: {e}")
        raise


def _fallback_keyword_ranking(
    prompt: str, 
    products: List[Dict[str, Any]], 
    max_results: int
) -> List[Dict[str, Any]]:
    """
    Fallback keyword-based ranking when AI fails
    """
    try:
        # Enhanced keyword matching with semantic understanding
        prompt_lower = prompt.lower()
        keywords = prompt_lower.split()
        
        # Define keyword categories for better matching
        crime_keywords = ["crime", "true crime", "murder", "mystery", "detective", "investigation", "criminal", "law", "justice"]
        entertainment_keywords = ["entertainment", "streaming", "video", "movie", "show", "series", "drama", "thriller", "documentary"]
        tech_keywords = ["tech", "technology", "mobile", "digital", "app", "software", "startup", "innovation"]
        sports_keywords = ["sports", "athletic", "fitness", "game", "competition", "team", "player"]
        
        scored_products = []
        
        for product in products:
            score = 0.0
            
            # Check product name
            if product.get("name"):
                name_lower = product["name"].lower()
                for keyword in keywords:
                    if keyword in name_lower:
                        score += 2.0  # Higher weight for name matches
            
            # Check description
            if product.get("description"):
                desc_lower = product["description"].lower()
                for keyword in keywords:
                    if keyword in desc_lower:
                        score += 1.0
            
            # Semantic matching for "true crime"
            if "true crime" in prompt_lower or "crime" in prompt_lower:
                # Boost entertainment and streaming products
                if any(word in product.get("name", "").lower() for word in ["entertainment", "streaming", "video", "movie", "show"]):
                    score += 3.0
                if any(word in product.get("description", "").lower() for word in ["entertainment", "streaming", "video", "movie", "show"]):
                    score += 2.0
            
            # Check categories
            if product.get("categories"):
                for category in product["categories"]:
                    category_lower = category.lower()
                    for keyword in keywords:
                        if keyword in category_lower:
                            score += 0.5
            
            # Add base score and price factor
            product["score"] = score + 0.1  # Base score
            if product.get("price_cpm"):
                product["price_factor"] = 1.0 / (1.0 + product["price_cpm"] / 1000.0)
            else:
                product["price_factor"] = 0.5
            
            scored_products.append(product)
        
        # Sort by score (descending) and price (ascending)
        scored_products.sort(
            key=lambda x: (x["score"], -x.get("price_factor", 0)), 
            reverse=True
        )
        
        # Return top results
        return scored_products[:max_results]
        
    except Exception as e:
        logger.error(f"Fallback ranking error: {e}")
        return products[:max_results] if products else []


def _create_response(
    agent_id: str,
    tenant_id: str,
    products: List[Dict[str, Any]],
    total_found: int,
    start_time: float,
    error_message: Optional[str] = None,
    execution_time_ms: Optional[int] = None
) -> tuple:
    """
    Create standardized response
    """
    if execution_time_ms is None:
        execution_time_ms = int((time.time() - start_time) * 1000)
    
    response_data = {
        "agent_id": agent_id,
        "tenant_id": tenant_id,
        "products": products,
        "total_found": total_found,
        "execution_time_ms": execution_time_ms,
        "status": "error" if error_message else "active",
        "error_message": error_message
    }
    
    status_code = 500 if error_message else 200
    return jsonify(response_data), status_code


@agent_providers_bp.route("/<tenant_id>/agent/<agent_type>/health", methods=["GET"])
def agent_health(tenant_id: str, agent_type: str):
    """
    Health check endpoint for agents
    """
    try:
        agent_id = f"{tenant_id}_{agent_type}"
        agent = agent_management_service.get_agent_details(agent_id, tenant_id)
        
        if not agent:
            return jsonify({
                "agent_id": agent_id,
                "tenant_id": tenant_id,
                "status": "not_found",
                "message": "Agent not found"
            }), 404
        
        return jsonify({
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "status": agent.status.value,
            "type": agent.type,
            "name": agent.name,
            "endpoint_url": agent.endpoint_url,
            "config": agent.config,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in agent health check: {e}")
        return jsonify({
            "agent_id": f"{tenant_id}_{agent_type}",
            "tenant_id": tenant_id,
            "status": "error",
            "error": str(e)
        }), 500
