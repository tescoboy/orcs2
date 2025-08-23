"""Service for AI-powered product ranking using tenant-specific prompts."""

import json
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal

from .ai_ranking_core import AIRankingCore
from .prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class AIRankingService(AIRankingCore):
    """Service for ranking products using AI with tenant-specific prompts."""
    
    def __init__(self):
        self.prompt_loader = PromptLoader()
    
    def rank_products(self, tenant_id: str, prompt: str, products: List[Dict[str, Any]], 
                     max_results: int = 10, locale: Optional[str] = None, 
                     currency: Optional[str] = None) -> List[Dict[str, Any]]:
        """Rank products using AI with tenant-specific prompt template."""
        try:
            # Load tenant-specific prompt template
            template = self.prompt_loader.get_tenant_prompt(tenant_id)
            
            # Prepare context for prompt compilation
            context = {
                "PROMPT": prompt,
                "PRODUCTS_JSON": json.dumps(products, default=str),
                "MAX_RESULTS": str(max_results)
            }
            
            if locale:
                context["LOCALE"] = f"Locale: {locale}\n"
            else:
                context["LOCALE"] = ""
            
            if currency:
                context["CURRENCY"] = f"Currency: {currency}\n"
            else:
                context["CURRENCY"] = ""
            
            # Compile the prompt
            compiled_prompt = self.prompt_loader.compile_prompt(template, context)
            
            # Call Gemini to get rankings
            rankings = self._call_gemini(compiled_prompt, products)
            
            # Apply rankings to products
            ranked_products = self._apply_rankings(products, rankings)
            
            # Limit to max_results
            return ranked_products[:max_results]
            
        except Exception as e:
            logger.error(f"Error ranking products for tenant {tenant_id}: {e}")
            # Return products without ranking on error
            return products[:max_results]


# Convenience function for easy access
def select_products_for_tenant(tenant_id: str, prompt: str, products: List[Dict[str, Any]], 
                              max_results: int = 10, locale: Optional[str] = None, 
                              currency: Optional[str] = None) -> List[Dict[str, Any]]:
    """Select and rank products for a tenant using AI."""
    service = AIRankingService()
    return service.rank_products(tenant_id, prompt, products, max_results, locale, currency)
