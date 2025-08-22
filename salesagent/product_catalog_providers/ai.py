"""AI-powered product catalog provider using Gemini for intelligent matching."""

import json
import os
from typing import Any

import google.generativeai as genai

from src.core.database.database_session import get_db_session
from src.core.database.models import Product as ProductModel
from src.core.schemas import Product

from .base import ProductCatalogProvider


class AIProductCatalog(ProductCatalogProvider):
    """
    AI-powered product catalog that uses Gemini to intelligently match
    products to briefs, simulating a RAG-like system.

    This provider:
    1. Fetches all available products from the database
    2. Uses Gemini to analyze the brief and rank/filter products
    3. Returns the most relevant products based on the AI's analysis

    Configuration:
        model: Gemini model to use (default: "gemini-1.5-flash")
        max_products: Maximum number of products to return (default: 5)
        temperature: Model temperature for creativity (default: 0.3)
        include_reasoning: Include AI reasoning in response (default: false)
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.model_name = config.get("model", "gemini-1.5-flash")
        self.max_products = config.get("max_products", 5)
        self.temperature = config.get("temperature", 0.3)
        self.include_reasoning = config.get("include_reasoning", False)

        # Initialize Gemini
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required for AI product catalog")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)

    async def get_products(
        self,
        brief: str,
        tenant_id: str,
        principal_id: str | None = None,
        context: dict[str, Any] | None = None,
        principal_data: dict[str, Any] | None = None,
    ) -> list[Product]:
        """
        Get products that match the given brief using AI analysis.

        Args:
            brief: Natural language description of what the advertiser is looking for
            tenant_id: The tenant ID to fetch products for
            principal_id: Optional principal ID for personalization
            context: Additional context for the analysis
            principal_data: Principal/advertiser specific data for personalization
        """
        # Get all available products
        all_products = await self._get_all_products(tenant_id)

        if not all_products:
            return []

        if not brief or brief.strip() == "":
            # Return all products if no brief provided
            return all_products[: self.max_products]

        # Use AI to analyze and rank products
        try:
            relevant_products = await self._analyze_products_with_ai(brief, all_products, context, principal_data)
            return relevant_products[: self.max_products]
        except Exception as e:
            print(f"AI analysis failed: {e}")
            # Fallback to returning all products if AI fails
            return all_products[: self.max_products]

    async def _get_all_products(self, tenant_id: str) -> list[Product]:
        """Fetch all products from the database."""
        with get_db_session() as session:
            product_models = session.query(ProductModel).filter_by(tenant_id=tenant_id).all()

            products = []
            for product_model in product_models:
                # Convert model to Product schema
                product_data = {
                    "product_id": product_model.product_id,
                    "name": product_model.name,
                    "description": product_model.description,
                    "formats": product_model.formats,
                    "targeting_template": product_model.targeting_template,
                    "delivery_type": product_model.delivery_type,
                    "is_fixed_price": product_model.is_fixed_price,
                    "cpm": float(product_model.cpm) if product_model.cpm else None,
                    "price_guidance": product_model.price_guidance,
                    "is_custom": product_model.is_custom,
                    "expires_at": product_model.expires_at,
                    "countries": product_model.countries,
                    "implementation_config": product_model.implementation_config,
                }

                # Create Product instance
                product = Product(**product_data)
                products.append(product)

            return products

    async def _analyze_products_with_ai(
        self,
        brief: str,
        products: list[Product],
        context: dict[str, Any] | None,
        principal_data: dict[str, Any] | None,
    ) -> list[Product]:
        """Use AI to analyze and rank products based on the brief."""

        # Prepare products data for AI analysis
        products_data = []
        for product in products:
            product_info = {
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "formats": product.formats,
                "delivery_type": product.delivery_type,
                "is_fixed_price": product.is_fixed_price,
                "cpm": product.cpm,
                "price_guidance": product.price_guidance,
                "countries": product.countries,
            }
            products_data.append(product_info)

        # Build context string
        context_str = ""
        if context:
            context_str = f"Additional context: {json.dumps(context, indent=2)}\n"

        if principal_data:
            context_str += f"Advertiser data: {json.dumps(principal_data, indent=2)}\n"

        # Create the AI prompt
        prompt = f"""
You are an expert media buyer analyzing products for a programmatic advertising campaign.

{context_str}

Campaign Brief: {brief}

Available Products:
{json.dumps(products_data, indent=2)}

Your task:
1. Analyze each product's relevance to the campaign brief
2. Consider targeting capabilities, format compatibility, and pricing
3. Rank products from most to least relevant
4. Return the top {self.max_products} products

Response format (JSON only):
{{
  "products": [
    {{
      "product_id": "product_id_here",
      "relevance_score": 0.95,
      "reasoning": "Why this product is relevant"
    }}
  ]
}}

Focus on:
- Targeting alignment with brief requirements
- Format suitability for campaign goals
- Pricing compatibility with budget
- Geographic targeting match
- Delivery type appropriateness

Return ONLY the JSON response, no additional text.
"""

        try:
            # Generate AI response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=self.temperature, max_output_tokens=2048),
            )

            # Parse AI response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "")
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "")

            response_text = response_text.strip()

            ai_result = json.loads(response_text)

            # Extract ranked product IDs
            ranked_product_ids = []
            for product_analysis in ai_result.get("products", []):
                ranked_product_ids.append(product_analysis["product_id"])

            # Reorder products based on AI ranking
            ranked_products = []
            for product_id in ranked_product_ids:
                for product in products:
                    if product.product_id == product_id:
                        # Add AI reasoning if requested
                        if self.include_reasoning:
                            for analysis in ai_result.get("products", []):
                                if analysis["product_id"] == product_id:
                                    product.ai_reasoning = analysis.get("reasoning", "")
                                    product.ai_score = analysis.get("relevance_score", 0)
                        ranked_products.append(product)
                        break

            return ranked_products

        except Exception as e:
            print(f"Error in AI analysis: {e}")
            # Return original products if AI analysis fails
            return products
