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
            import os
            import google.generativeai as genai
            
            # Get Gemini API key
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY environment variable not set")
                return self._get_fallback_rankings(products)
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            
            logger.info(f"Calling Gemini API with prompt length: {len(prompt)}")
            logger.info(f"Ranking {len(products)} products")
            
            # Call Gemini
            response = model.generate_content(prompt)
            response_text = response.text
            
            logger.info(f"Gemini response received: {len(response_text)} characters")
            
            # Parse and clean the response
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Parse JSON response
            ai_response = json.loads(response_text.strip())
            
            logger.info(f"Successfully parsed Gemini response with {len(ai_response.get('products', []))} ranked products")
            return ai_response.get("products", [])
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            logger.info("Falling back to mock rankings")
            return self._get_fallback_rankings(products)
    
    def _get_fallback_rankings(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get fallback rankings when Gemini is not available."""
        rankings = []
        for i, product in enumerate(products):
            rankings.append({
                "product_id": product.get("id", f"product_{i}"),
                "relevance_score": 1.0 - (i * 0.1),  # Decreasing scores
                "reasoning": f"Fallback ranking position {i+1}"
            })
        return rankings
    
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
