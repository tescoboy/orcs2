#!/usr/bin/env python3
"""Test orchestrator service directly."""

import os
os.environ['DATABASE_URL'] = 'sqlite:////Users/harvingupta/.adcp/adcp.db'

from orchestrator.orchestrator_service import OrchestratorService
from schemas.orchestrator.request import BuyerOrchestrateRequest

def main():
    print("Testing orchestrator service...")
    
    try:
        # Create orchestrator service
        orchestrator = OrchestratorService()
        
        # Create test request
        request = BuyerOrchestrateRequest(
            prompt="display banner",
            max_results=10
        )
        
        # Call orchestrator
        print("Calling orchestrator...")
        response = orchestrator.orchestrate(request)
        
        print(f"Response: {response}")
        print(f"Total products: {response.get('total', 0)}")
        print(f"Products: {len(response.get('products', []))}")
        
        for i, product in enumerate(response.get('products', [])[:3]):
            print(f"Product {i+1}: {product.get('name')} from {product.get('publisher_name')}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
