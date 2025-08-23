#!/usr/bin/env python3
"""Fix database by adding missing AI prompt template columns."""

import sqlite3
import os

def main():
    db_path = "orcs2.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(tenants)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print("Current columns in tenants table:")
        for col in columns:
            print(f"  - {col}")
        
        # Add missing columns
        if 'ai_prompt_template' not in columns:
            print("Adding ai_prompt_template column...")
            cursor.execute("ALTER TABLE tenants ADD COLUMN ai_prompt_template TEXT")
        
        if 'ai_prompt_updated_at' not in columns:
            print("Adding ai_prompt_updated_at column...")
            cursor.execute("ALTER TABLE tenants ADD COLUMN ai_prompt_updated_at DATETIME")
        
        # Check if there are any tenants
        cursor.execute("SELECT COUNT(*) FROM tenants")
        tenant_count = cursor.fetchone()[0]
        print(f"\nFound {tenant_count} tenants in database")
        
        if tenant_count == 0:
            print("Creating a default tenant...")
            cursor.execute("""
                INSERT INTO tenants (name, subdomain, created_at, updated_at, is_active)
                VALUES ('Default Publisher', 'default', datetime('now'), datetime('now'), 1)
            """)
            tenant_id = cursor.lastrowid
            print(f"Created default tenant with ID: {tenant_id}")
        
        conn.commit()
        print("\n✅ Database fixed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
