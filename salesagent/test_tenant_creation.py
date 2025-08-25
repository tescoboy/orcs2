#!/usr/bin/env python3
"""Test script to verify tenant creation works with fixed Principal model."""

import os
import sys
import json
from datetime import datetime, timezone

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant, Principal

def test_tenant_creation():
    """Test creating a tenant with proper Principal creation."""
    print("🧪 Testing tenant creation...")
    
    try:
        with get_db_session() as db_session:
            # Test tenant data
            tenant_id = "test_tenant_creation"
            tenant_name = "Test Tenant Creation"
            
            # Check if tenant already exists
            existing = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if existing:
                print(f"⚠️  Tenant {tenant_id} already exists, deleting...")
                db_session.delete(existing)
                db_session.commit()
            
            # Create new tenant
            new_tenant = Tenant(
                tenant_id=tenant_id,
                name=tenant_name,
                subdomain="test_tenant_creation",
                is_active=True,
                ad_server="mock",
                billing_plan="standard",
                max_daily_budget=10000.0,
                enable_aee_signals=True,
                human_review_required=False,
                admin_token="test_token_12345",
                authorized_emails=json.dumps([]),
                authorized_domains=json.dumps([]),
                auto_approve_formats=json.dumps(["display_300x250"]),
                policy_settings=json.dumps({"enabled": False, "require_approval": False, "max_daily_budget": None, "blocked_categories": [], "allowed_advertisers": [], "custom_rules": {}}),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            
            db_session.add(new_tenant)
            print("✅ Tenant created successfully")
            
            # Create default principal
            default_platform_mapping = {
                "mock": {
                    "advertiser_id": f"mock_{tenant_id}",
                    "advertiser_name": f"{tenant_name} Mock Advertiser"
                }
            }
            
            default_principal = Principal(
                tenant_id=tenant_id,
                principal_id=f"{tenant_id}_default",
                name=f"{tenant_name} Default Principal",
                access_token="test_token_12345",
                platform_mappings=json.dumps(default_platform_mapping),
            )
            
            db_session.add(default_principal)
            print("✅ Principal created successfully")
            
            # Commit the transaction
            db_session.commit()
            print("✅ Database transaction committed successfully")
            
            # Verify the data was saved correctly
            saved_tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            saved_principal = db_session.query(Principal).filter_by(tenant_id=tenant_id, principal_id=f"{tenant_id}_default").first()
            
            if saved_tenant and saved_principal:
                print("✅ Verification successful:")
                print(f"   Tenant: {saved_tenant.name} (ID: {saved_tenant.tenant_id})")
                print(f"   Principal: {saved_principal.name} (ID: {saved_principal.principal_id})")
                print(f"   Platform mappings: {saved_principal.platform_mappings}")
                return True
            else:
                print("❌ Verification failed - data not found in database")
                return False
                
    except Exception as e:
        print(f"❌ Error during tenant creation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Clean up test data."""
    print("🧹 Cleaning up test data...")
    
    try:
        with get_db_session() as db_session:
            # Delete test tenant and its principal
            tenant_id = "test_tenant_creation"
            
            # Delete principal first (due to foreign key constraint)
            principal = db_session.query(Principal).filter_by(tenant_id=tenant_id).first()
            if principal:
                db_session.delete(principal)
                print("✅ Test principal deleted")
            
            # Delete tenant
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if tenant:
                db_session.delete(tenant)
                print("✅ Test tenant deleted")
            
            db_session.commit()
            print("✅ Cleanup completed")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    print("🚀 Starting tenant creation test...")
    
    # Run the test
    success = test_tenant_creation()
    
    if success:
        print("\n🎉 TEST PASSED: Tenant creation works correctly!")
    else:
        print("\n💥 TEST FAILED: Tenant creation has issues!")
    
    # Clean up
    cleanup_test_data()
    
    print("\n✅ Test completed!")
