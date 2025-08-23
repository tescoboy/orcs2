#!/usr/bin/env python3
"""Migration script to add buyer campaign tables."""

import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def migrate_buyer_campaigns():
    """Add buyer campaign tables to the database."""
    
    # Get database path
    db_path = os.getenv('DATABASE_URL', 'sqlite:///orcs2.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path.replace('sqlite:///', '')
    else:
        print("Error: Only SQLite databases are supported for this migration")
        return False
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables already exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='buyer_campaigns'
        """)
        
        if cursor.fetchone():
            print("✓ buyer_campaigns table already exists")
        else:
            # Create buyer_campaigns table
            cursor.execute("""
                CREATE TABLE buyer_campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    objective TEXT,
                    budget_total DECIMAL(10,2) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft' 
                        CHECK (status IN ('draft', 'active', 'paused', 'archived')),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✓ Created buyer_campaigns table")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='buyer_campaign_products'
        """)
        
        if cursor.fetchone():
            print("✓ buyer_campaign_products table already exists")
        else:
            # Create buyer_campaign_products table
            cursor.execute("""
                CREATE TABLE buyer_campaign_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL,
                    product_id TEXT NOT NULL,
                    publisher_tenant_id TEXT NOT NULL,
                    source_agent_id TEXT,
                    price_cpm DECIMAL(10,2) NOT NULL,
                    quantity INTEGER,
                    snapshot_json TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (campaign_id) REFERENCES buyer_campaigns (id) ON DELETE CASCADE
                )
            """)
            print("✓ Created buyer_campaign_products table")
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_buyer_campaigns_status 
            ON buyer_campaigns (status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_buyer_campaign_products_campaign_id 
            ON buyer_campaign_products (campaign_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_buyer_campaign_products_publisher 
            ON buyer_campaign_products (publisher_tenant_id)
        """)
        
        print("✓ Created indexes for buyer campaign tables")
        
        conn.commit()
        conn.close()
        
        print("🎉 Buyer campaign migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_buyer_campaigns()
    sys.exit(0 if success else 1)
