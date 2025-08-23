#!/usr/bin/env python3
"""Migration script to add AI prompt template support to tenants table.

This script adds:
- ai_prompt_template (TEXT nullable) - Custom AI prompt template per tenant
- ai_prompt_updated_at (DATETIME nullable) - Audit timestamp for prompt changes

The migration is idempotent and safe to run multiple times.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def migrate_database(db_path: str = "data/salesagent.db") -> dict:
    """Add AI prompt template fields to tenants table.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        dict: Migration summary with changes made
    """
    
    # Ensure db directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "changes_made": [],
        "warnings": [],
        "errors": [],
        "migration_time": datetime.now().isoformat()
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tenants table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tenants'
        """)
        
        if not cursor.fetchone():
            logger.warning("Tenants table does not exist, creating it")
            summary["warnings"].append("Tenants table did not exist")
            # Create basic tenants table (this would be handled by main schema creation)
            cursor.execute("""
                CREATE TABLE tenants (
                    tenant_id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    subdomain VARCHAR(100) UNIQUE NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            summary["changes_made"].append("Created tenants table")
        
        # Check if ai_prompt_template column exists
        cursor.execute("PRAGMA table_info(tenants)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "ai_prompt_template" not in columns:
            logger.info("Adding ai_prompt_template column to tenants table")
            cursor.execute("""
                ALTER TABLE tenants 
                ADD COLUMN ai_prompt_template TEXT
            """)
            summary["changes_made"].append("Added ai_prompt_template column")
        else:
            logger.info("ai_prompt_template column already exists")
        
        if "ai_prompt_updated_at" not in columns:
            logger.info("Adding ai_prompt_updated_at column to tenants table")
            cursor.execute("""
                ALTER TABLE tenants 
                ADD COLUMN ai_prompt_updated_at DATETIME
            """)
            summary["changes_made"].append("Added ai_prompt_updated_at column")
        else:
            logger.info("ai_prompt_updated_at column already exists")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(tenants)")
        final_columns = [row[1] for row in cursor.fetchall()]
        
        if "ai_prompt_template" in final_columns and "ai_prompt_updated_at" in final_columns:
            summary["changes_made"].append("Verified new columns exist")
            logger.info("Migration completed successfully")
        else:
            error_msg = "Failed to verify new columns after migration"
            summary["errors"].append(error_msg)
            logger.error(error_msg)
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        error_msg = f"Migration failed: {str(e)}"
        summary["errors"].append(error_msg)
        logger.error(error_msg)
        
        if 'conn' in locals():
            conn.rollback()
            conn.close()
    
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run migration
    result = migrate_database()
    
    print("Migration Summary:")
    print(f"Time: {result['migration_time']}")
    
    if result["changes_made"]:
        print("\nChanges made:")
        for change in result["changes_made"]:
            print(f"  ✓ {change}")
    
    if result["warnings"]:
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"  ⚠ {warning}")
    
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  ✗ {error}")
        exit(1)
    
    print("\n✅ Migration completed successfully!")
