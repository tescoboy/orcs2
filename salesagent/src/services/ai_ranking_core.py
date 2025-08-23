"""Core AI ranking functionality."""

import json
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class AIRankingCore:
    """Core functionality for AI-powered product ranking."""
    
    def _call_gemini(self, prompt: str, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Call Gemini API to rank products."""
        try:
            # Mock Gemini call for now - in real implementation, this would call the actual API
            # For testing purposes, we'll simulate a response
            logger.debug(f"Calling Gemini with prompt length: {len(prompt)}")
            logger.debug(f"Ranking {len(products)} products")
            
            # Simulate AI response - in real implementation, this would be the actual Gemini response
            mock_response = {
                "products": [
                    {
                        "product_id": products[0]["id"] if products else "unknown",
                        "relevance_score": 0.95,
                        "reasoning": "Perfect match for campaign requirements"
                    }
                ]
            }
            
            # Parse and clean the response
            if isinstance(mock_response, str):
                # Remove markdown code blocks if present
                if mock_response.startswith("```json"):
                    mock_response = mock_response[7:]
                if mock_response.endswith("```"):
                    mock_response = mock_response[:-3]
                mock_response = json.loads(mock_response.strip())
            
            return mock_response.get("products", [])
            
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return []
    
    def _apply_rankings(self, products: List[Dict[str, Any]], rankings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply AI rankings to products."""
        # Create a lookup for rankings by product_id
        ranking_lookup = {r["product_id"]: r for r in rankings}
        
        for product in products:
            product_id = product.get("id")
            if product_id in ranking_lookup:
                ranking = ranking_lookup[product_id]
                product["score"] = Decimal(str(ranking.get("relevance_score", 0.0)))
                product["rationale"] = ranking.get("reasoning", "")
            else:
                product["score"] = Decimal("0.0")
                product["rationale"] = "No AI ranking available"
        
        # Sort by score descending
        products.sort(key=lambda p: p.get("score", Decimal("0.0")), reverse=True)
        
        logger.debug(f"Applied rankings to {len(products)} products")
        return products
