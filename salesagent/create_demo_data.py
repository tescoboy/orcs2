#!/usr/bin/env python3
"""
Create demo data for the multi-agent orchestrator
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant, Principal
from src.services.agent_management_service import agent_management_service
from src.core.schemas.agent import AgentStatus
from datetime import datetime, UTC

def create_demo_tenants():
    """Create demo tenants with agents"""
    
    with get_db_session() as db_session:
        # Sample tenants data
        demo_tenants = [
            {
                "tenant_id": "tech_publisher",
                "name": "Tech Publisher Inc",
                "description": "Technology-focused publisher with AI-powered products",
                "agents": {
                    "tech_ai_agent": {
                        "name": "Tech AI Agent",
                        "type": "local_ai",
                        "status": "active",
                        "endpoint_url": "/tenant/tech_publisher/agent/local_ai",
                        "config": {
                            "model": "gemini-2.0-flash-exp",
                            "specialization": "technology_products"
                        }
                    },
                    "tech_mcp_agent": {
                        "name": "Tech MCP Agent",
                        "type": "mcp",
                        "status": "active",
                        "endpoint_url": "https://tech-mcp-agent.example.com/api",
                        "config": {
                            "api_key": "demo_api_key",
                            "specialization": "mobile_technology"
                        }
                    }
                }
            },
            {
                "tenant_id": "sports_publisher",
                "name": "Sports Media Network",
                "description": "Sports and entertainment publisher",
                "agents": {
                    "sports_ai_agent": {
                        "name": "Sports AI Agent",
                        "type": "local_ai",
                        "status": "active",
                        "endpoint_url": "/tenant/sports_publisher/agent/local_ai",
                        "config": {
                            "model": "gemini-2.0-flash-exp",
                            "specialization": "sports_products"
                        }
                    }
                }
            },
            {
                "tenant_id": "entertainment_publisher",
                "name": "Entertainment Hub",
                "description": "Entertainment and streaming content publisher",
                "agents": {
                    "entertainment_ai_agent": {
                        "name": "Entertainment AI Agent",
                        "type": "local_ai",
                        "status": "active",
                        "endpoint_url": "/tenant/entertainment_publisher/agent/local_ai",
                        "config": {
                            "model": "gemini-2.0-flash-exp",
                            "specialization": "entertainment_products"
                        }
                    },
                    "streaming_mcp_agent": {
                        "name": "Streaming MCP Agent",
                        "type": "mcp",
                        "status": "active",
                        "endpoint_url": "https://streaming-mcp-agent.example.com/api",
                        "config": {
                            "api_key": "demo_api_key",
                            "specialization": "streaming_services"
                        }
                    }
                }
            }
        ]
        
        created_tenants = []
        
        for tenant_data in demo_tenants:
            # Check if tenant already exists
            existing_tenant = db_session.query(Tenant).filter(
                Tenant.tenant_id == tenant_data["tenant_id"]
            ).first()
            
            if existing_tenant:
                print(f"Tenant {tenant_data['name']} already exists, updating...")
                tenant = existing_tenant
            else:
                print(f"Creating tenant: {tenant_data['name']}")
                tenant = Tenant(
                    tenant_id=tenant_data["tenant_id"],
                    name=tenant_data["name"],
                    subdomain=tenant_data["tenant_id"],  # Use tenant_id as subdomain
                    is_active=True,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                db_session.add(tenant)
            
            # Create principal for the tenant
            principal = db_session.query(Principal).filter(
                Principal.tenant_id == tenant_data["tenant_id"]
            ).first()
            
            if not principal:
                principal = Principal(
                    tenant_id=tenant_data["tenant_id"],
                    principal_id=f"{tenant_data['tenant_id']}_principal",
                    name=f"{tenant_data['name']} Principal",
                    platform_mappings={"mock": {"demo_platform": "demo_mapping"}},
                    access_token=f"demo_token_{tenant_data['tenant_id']}"
                )
                db_session.add(principal)
            
            # Set tenant config with agents in policy_settings
            import json
            # Force update policy_settings to include agents
            tenant.policy_settings = json.dumps({
                "agents": tenant_data["agents"],
                "settings": {
                    "default_locale": "en-US",
                    "default_currency": "USD"
                }
            })
            print(f"Updated policy_settings for {tenant.name}: {str(tenant.policy_settings)[:100]}...")
            
            created_tenants.append(tenant)
        
        # Commit changes
        db_session.commit()
        
        print(f"\n✅ Created/Updated {len(created_tenants)} tenants:")
        for tenant in created_tenants:
            import json
            config = {}
            if tenant.policy_settings:
                try:
                    config = json.loads(tenant.policy_settings)
                except (json.JSONDecodeError, TypeError):
                    config = {}
            agent_count = len(config.get("agents", {}))
            print(f"  - {tenant.name} ({tenant.tenant_id}): {agent_count} agents")
        
        return created_tenants

def create_sample_products():
    """Create sample products for testing"""
    
    with get_db_session() as db_session:
        # Sample products data
        sample_products = [
            {
                "product_id": "tech_mobile_banner",
                "name": "Mobile Tech Banner",
                "description": "High-performance mobile banner for technology products",
                "price_cpm": 8.50,
                "formats": ["display", "banner"],
                "categories": "technology,mobile",
                "targeting": "US,CA",
                "image_url": "https://example.com/tech_banner.jpg",
                "delivery_type": "standard",
                "tenant_id": "tech_publisher"
            },
            {
                "product_id": "sports_video_ad",
                "name": "Sports Video Advertisement",
                "description": "Engaging video ad for sports content",
                "price_cpm": 12.00,
                "formats": ["video", "display"],
                "categories": "sports,entertainment",
                "targeting": "US,UK",
                "image_url": "https://example.com/sports_video.jpg",
                "delivery_type": "premium",
                "tenant_id": "sports_publisher"
            },
            {
                "product_id": "entertainment_streaming",
                "name": "Streaming Service Promotion",
                "description": "Promotional ad for streaming services",
                "price_cpm": 15.00,
                "formats": ["video", "display", "banner"],
                "categories": "entertainment,streaming",
                "targeting": "US,CA,UK",
                "image_url": "https://example.com/streaming_ad.jpg",
                "delivery_type": "premium",
                "tenant_id": "entertainment_publisher"
            }
        ]
        
        from src.core.database.models import Product
        
        created_products = []
        
        for product_data in sample_products:
            # Check if product already exists
            existing_product = db_session.query(Product).filter(
                Product.product_id == product_data["product_id"]
            ).first()
            
            if existing_product:
                print(f"Product {product_data['name']} already exists, updating...")
                product = existing_product
            else:
                print(f"Creating product: {product_data['name']}")
                product = Product(
                    product_id=product_data["product_id"],
                    name=product_data["name"],
                    description=product_data["description"],
                    cpm=product_data["price_cpm"],
                    formats=product_data["formats"],
                    targeting_template={"geo_targets": product_data["targeting"].split(",")},
                    delivery_type=product_data["delivery_type"],
                    is_fixed_price=True,
                    tenant_id=product_data["tenant_id"]
                )
                db_session.add(product)
            
            created_products.append(product)
        
        # Commit changes
        db_session.commit()
        
        print(f"\n✅ Created/Updated {len(created_products)} products:")
        for product in created_products:
            print(f"  - {product.name} (${product.cpm} CPM)")
        
        return created_products

def main():
    """Main function to create demo data"""
    print("🚀 Creating demo data for multi-agent orchestrator...")
    
    try:
        # Create tenants with agents
        tenants = create_demo_tenants()
        
        # Create sample products
        products = create_sample_products()
        
        print(f"\n🎉 Demo data created successfully!")
        print(f"📊 Summary:")
        print(f"  - Tenants: {len(tenants)}")
        print(f"  - Products: {len(products)}")
        
        # Test agent discovery
        print(f"\n🔍 Testing agent discovery...")
        agents = agent_management_service.discover_active_agents()
        print(f"  - Active agents found: {len(agents)}")
        
        for agent, tenant_id, tenant_name in agents:
            print(f"    - {agent.name} ({agent.type}) in {tenant_name}")
        
        print(f"\n✅ Demo setup complete! You can now test the orchestrator.")
        print(f"🌐 Visit: http://localhost:8000/demo")
        print(f"🔍 Test search: http://localhost:8000/buyer/")
        
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
