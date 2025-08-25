"""
Product Normalization and Deduplication
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class ProductNormalizer:
    """Normalize and deduplicate products from multiple agents"""
    
    def __init__(self):
        self.required_fields = [
            "product_id", "name", "description", "price_cpm", 
            "publisher_tenant_id", "source_agent_id"
        ]
        
        self.optional_fields = [
            "score", "formats", "categories", "targeting", 
            "image_url", "delivery_type", "rationale", "merchandising_blurb"
        ]
    
    def normalize_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize product format and ensure all required fields are present
        """
        normalized_products = []
        
        for product in products:
            try:
                normalized = self._normalize_single_product(product)
                if normalized:
                    normalized_products.append(normalized)
            except Exception as e:
                logger.warning(f"Failed to normalize product {product.get('product_id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Normalized {len(normalized_products)} products from {len(products)} input products")
        return normalized_products
    
    def _normalize_single_product(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize a single product
        """
        try:
            normalized = {}
            
            # Required fields with defaults
            normalized["product_id"] = str(product.get("product_id", ""))
            normalized["name"] = str(product.get("name", "Unknown Product"))
            normalized["description"] = str(product.get("description", ""))
            normalized["price_cpm"] = float(product.get("price_cpm", 0.0))
            normalized["publisher_tenant_id"] = str(product.get("publisher_tenant_id", ""))
            normalized["source_agent_id"] = str(product.get("source_agent_id", ""))
            
            # Validate required fields
            if not normalized["product_id"] or not normalized["publisher_tenant_id"]:
                logger.warning(f"Product missing required fields: {product}")
                return None
            
            # Optional fields with defaults
            normalized["score"] = float(product.get("score", 0.0))
            normalized["formats"] = self._normalize_list_field(product.get("formats", []))
            normalized["categories"] = self._normalize_list_field(product.get("categories", []))
            normalized["targeting"] = self._normalize_list_field(product.get("targeting", []))
            # Handle image_url properly - keep None as None, not convert to string "None"
            image_url = product.get("image_url")
            normalized["image_url"] = image_url if image_url else None
            normalized["delivery_type"] = str(product.get("delivery_type", "standard"))
            normalized["rationale"] = str(product.get("rationale", ""))
            normalized["merchandising_blurb"] = str(product.get("merchandising_blurb", ""))
            
            # Add metadata
            normalized["normalized_at"] = datetime.now(UTC).isoformat()
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing product: {e}")
            return None
    
    def _normalize_list_field(self, value: Any) -> List[str]:
        """
        Normalize a field that should be a list of strings
        """
        if isinstance(value, str):
            # Split by comma if it's a string
            return [item.strip() for item in value.split(",") if item.strip()]
        elif isinstance(value, list):
            # Convert all items to strings
            return [str(item).strip() for item in value if item]
        else:
            return []
    
    def deduplicate_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate products based on publisher_tenant_id + product_id
        Keep the product with the highest score
        """
        if not products:
            return []
        
        # Group by deduplication key
        product_groups = {}
        
        for product in products:
            dedup_key = f"{product.get('publisher_tenant_id', '')}_{product.get('product_id', '')}"
            
            if dedup_key not in product_groups:
                product_groups[dedup_key] = []
            
            product_groups[dedup_key].append(product)
        
        # Keep the best product from each group
        deduplicated = []
        
        for dedup_key, group in product_groups.items():
            if len(group) == 1:
                # No duplicates, keep as is
                deduplicated.append(group[0])
            else:
                # Multiple products with same key, keep the one with highest score
                best_product = max(group, key=lambda p: float(p.get("score", 0.0)))
                deduplicated.append(best_product)
                
                logger.info(f"Deduplicated {len(group)} products for key {dedup_key}, "
                           f"kept product with score {best_product.get('score', 0.0)}")
        
        logger.info(f"Deduplicated {len(products)} products to {len(deduplicated)} unique products")
        return deduplicated
    
    def sort_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort products by score (descending), price (ascending), then name (ascending)
        """
        if not products:
            return []
        
        def sort_key(product):
            score = float(product.get("score", 0.0))
            price = float(product.get("price_cpm", 0.0))
            name = str(product.get("name", "")).lower()
            
            # Primary: score (descending)
            # Secondary: price (ascending) 
            # Tertiary: name (ascending)
            return (-score, price, name)
        
        sorted_products = sorted(products, key=sort_key)
        
        logger.info(f"Sorted {len(sorted_products)} products")
        return sorted_products
    
    def truncate_products(self, products: List[Dict[str, Any]], max_results: int) -> List[Dict[str, Any]]:
        """
        Truncate products to max_results
        """
        if not products:
            return []
        
        truncated = products[:max_results]
        
        logger.info(f"Truncated {len(products)} products to {len(truncated)} results")
        return truncated
    
    def process_products(
        self, 
        products: List[Dict[str, Any]], 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Complete processing pipeline: normalize, deduplicate, sort, truncate
        """
        logger.info(f"Processing {len(products)} products with max_results={max_results}")
        
        # Step 1: Normalize
        normalized = self.normalize_products(products)
        
        # Step 2: Deduplicate
        deduplicated = self.deduplicate_products(normalized)
        
        # Step 3: Sort
        sorted_products = self.sort_products(deduplicated)
        
        # Step 4: Truncate
        final_products = self.truncate_products(sorted_products, max_results)
        
        logger.info(f"Processing complete: {len(products)} input -> {len(final_products)} output")
        return final_products


# Global instance
product_normalizer = ProductNormalizer()
