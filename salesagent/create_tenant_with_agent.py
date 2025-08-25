#!/usr/bin/env python3

import sys
from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant, Product
import json

def create_tenant_with_agent(tenant_id, tenant_name, product_name=None, product_description=None):
    """Create a new tenant with an agent and optionally a product"""
    with get_db_session() as db:
        # Check if tenant already exists
        existing_tenant = db.query(Tenant).filter_by(tenant_id=tenant_id).first()
        if existing_tenant:
            print(f"❌ Tenant '{tenant_id}' already exists!")
            return False
        
        # Create the tenant
        new_tenant = Tenant(
            tenant_id=tenant_id,
            name=tenant_name,
            is_active=True,
            subdomain=tenant_id,
            billing_plan="standard",
            max_daily_budget=10000,
            enable_aee_signals=True,
            human_review_required=True
        )
        
        # Create agent configuration
        agent_config = {
            "agents": {
                f"{tenant_id}_ai_agent": {
                    "name": f"{tenant_name} AI Agent",
                    "type": "local",
                    "status": "active",
                    "config": {
                        "model": "gemini-1.5-flash",
                        "specialization": "general"
                    }
                }
            },
            "settings": {
                "default_locale": "en-US",
                "default_currency": "USD"
            }
        }
        
        new_tenant.policy_settings = agent_config
        db.add(new_tenant)
        
        # Create a sample product if requested
        if product_name and product_description:
            sample_product = Product(
                product_id=f"{tenant_id}_sample_product",
                name=product_name,
                description=product_description,
                tenant_id=tenant_id,
                cpm=25.00,
                formats=["display", "banner"],
                targeting_template={},
                delivery_type="standard",
                is_fixed_price=True
            )
            db.add(sample_product)
            print(f"✅ Created sample product: {product_name}")
        
        db.commit()
        
        print(f"✅ Created tenant '{tenant_id}' with agent!")
        print(f"Tenant Name: {tenant_name}")
        print(f"Agent ID: {tenant_id}_ai_agent")
        print(f"Agent config: {json.dumps(agent_config, indent=2)}")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_tenant_with_agent.py <tenant_id> <tenant_name> [product_name] [product_description]")
        print("\nExample: python create_tenant_with_agent.py harvinads_hg 'Harvinads HG' 'True Crime Documentary' 'Exclusive true crime documentary advertising'")
        sys.exit(1)
    
    tenant_id = sys.argv[1]
    tenant_name = sys.argv[2]
    product_name = sys.argv[3] if len(sys.argv) > 3 else None
    product_description = sys.argv[4] if len(sys.argv) > 4 else None
    
    success = create_tenant_with_agent(tenant_id, tenant_name, product_name, product_description)
    if success:
        print(f"\n🎉 Tenant '{tenant_id}' created successfully with agent!")
        print("The tenant should now appear in orchestrator searches.")
    else:
        sys.exit(1)
