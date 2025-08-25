#!/usr/bin/env python3

import os
import sys
import json
from datetime import datetime

# Set the database URL
os.environ['DATABASE_URL'] = 'sqlite:///./adcp.db'

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database.database_session import get_db_session
from src.core.database.models import Product

def add_sample_products():
    sample_products = [
        {
            "product_id": "netflix_stranger_things",
            "tenant_id": "netflix",
            "name": "Netflix Stranger Things Exclusive",
            "description": "Exclusive sponsorship alongside Stranger Things, Netflix's global sci-fi phenomenon. Ideal for high-impact awareness campaigns tied to cultural moments.",
            "formats": json.dumps([{"name": "Video", "format_id": "video", "type": "video"}, {"name": "CTV", "format_id": "ctv", "type": "video"}]),
            "targeting_template": json.dumps({"geo": ["US", "CA", "GB"], "demographics": ["18-34"], "interests": ["entertainment", "sci-fi"]}),
            "cpm": 84.27,
            "delivery_type": "guaranteed",
            "is_fixed_price": True,
            "countries": json.dumps(["US", "CA", "GB"]),
            "implementation_config": json.dumps({"placement": "pre-roll", "duration": "30s", "viewability": "high"})
        },
        {
            "product_id": "tiktok_hashtag_challenge",
            "tenant_id": "tiktok",
            "name": "TikTok Trending Hashtag Challenge",
            "description": "Sponsored hashtag challenges that encourage user participation and viral content creation. Optimized for engagement, scale, and cultural relevance on TikTok.",
            "formats": json.dumps([{"name": "Video", "format_id": "video", "type": "video"}, {"name": "Social", "format_id": "social", "type": "native"}]),
            "targeting_template": json.dumps({"geo": ["US"], "demographics": ["13-24"], "interests": ["social_media", "trending"]}),
            "cpm": 10.76,
            "delivery_type": "guaranteed",
            "is_fixed_price": True,
            "countries": json.dumps(["US"]),
            "implementation_config": json.dumps({"placement": "feed", "duration": "15s", "engagement": "high"})
        },
        {
            "product_id": "youtube_premium_video",
            "tenant_id": "youtube",
            "name": "YouTube Premium Video Pre-roll",
            "description": "High-quality video pre-roll advertising on YouTube with premium placement and targeting capabilities.",
            "formats": json.dumps([{"name": "Video", "format_id": "video", "type": "video"}, {"name": "Pre-roll", "format_id": "pre_roll", "type": "video"}]),
            "targeting_template": json.dumps({"geo": ["US", "CA"], "demographics": ["18-34"], "interests": ["entertainment", "education"]}),
            "cpm": 15.50,
            "delivery_type": "guaranteed",
            "is_fixed_price": True,
            "countries": json.dumps(["US", "CA"]),
            "implementation_config": json.dumps({"placement": "pre-roll", "duration": "20s", "skip_after": "5s"})
        },
        {
            "product_id": "netflix_bridgerton",
            "tenant_id": "netflix",
            "name": "Netflix Bridgerton Season Premiere",
            "description": "Exclusive sponsorship alongside Bridgerton, Netflix's flagship period drama. Ideal for driving awareness during high-profile streaming moments.",
            "formats": json.dumps([{"name": "CTV", "format_id": "ctv", "type": "video"}, {"name": "Video", "format_id": "video", "type": "video"}]),
            "targeting_template": json.dumps({"geo": ["US", "CA", "GB"], "demographics": ["18-54"], "interests": ["drama", "romance"]}),
            "cpm": 62.53,
            "delivery_type": "guaranteed",
            "is_fixed_price": True,
            "countries": json.dumps(["US", "CA", "GB"]),
            "implementation_config": json.dumps({"placement": "mid-roll", "duration": "30s", "viewability": "high"})
        },
        {
            "product_id": "tiktok_branded_effect",
            "tenant_id": "tiktok",
            "name": "TikTok Branded AR Effect",
            "description": "Custom augmented reality effects that users can apply to their videos, creating viral brand engagement.",
            "formats": json.dumps([{"name": "AR", "format_id": "ar", "type": "native"}, {"name": "Social", "format_id": "social", "type": "native"}]),
            "targeting_template": json.dumps({"geo": ["US"], "demographics": ["13-30"], "interests": ["creativity", "technology"]}),
            "cpm": 8.25,
            "delivery_type": "non_guaranteed",
            "is_fixed_price": False,
            "countries": json.dumps(["US"]),
            "implementation_config": json.dumps({"placement": "effect_gallery", "engagement": "high", "viral_potential": "high"})
        }
    ]
    
    with get_db_session() as session:
        for product_data in sample_products:
            try:
                # Check if product already exists
                existing = session.query(Product).filter_by(product_id=product_data["product_id"]).first()
                if not existing:
                    product = Product(**product_data)
                    session.add(product)
                    session.commit()
                    print(f"Added product: {product_data['name']} for {product_data['tenant_id']}")
                else:
                    print(f"Product already exists: {product_data['name']}")
            except Exception as e:
                print(f"Error adding {product_data['name']}: {e}")
                session.rollback()
        
        print("Sample products added successfully!")

if __name__ == "__main__":
    add_sample_products()
