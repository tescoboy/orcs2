# Database Access Patterns Guide

## Overview

The AdCP Sales Agent uses **SQLAlchemy ORM** for database operations. As of Issue #74, we are migrating all database access to use context managers with SQLAlchemy ORM, eliminating manual connection management and raw SQL queries.

## Migration Status

- ✅ **main.py**: Fully migrated (all MCP tools now use context managers)
- 🔄 **admin_ui.py**: Partially migrated (54 operations remaining)
- ⏳ **Other files**: 34 files still need migration

## ✅ RECOMMENDED: Use Context Manager Pattern

### For ORM Operations (PREFERRED)
```python
from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant, Principal

# CORRECT - Automatic cleanup, thread-safe
with get_db_session() as session:
    tenant = session.query(Tenant).filter_by(tenant_id=tenant_id).first()
    if tenant:
        tenant.name = "New Name"
        session.commit()  # Explicit commit required
    # Session automatically closed/cleaned up
```

### For Raw SQL Operations (When ORM Not Available)
```python
from src.core.database.db_config import get_db_connection

# CORRECT - Using context manager
with get_db_connection() as conn:
    cursor = conn.execute("SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,))
    result = cursor.fetchone()
    conn.commit()  # For write operations
    # Connection automatically closed
```

## ❌ AVOID: Manual Connection Management

### DO NOT USE - Prone to Leaks
```python
# WRONG - Manual management, prone to connection leaks
conn = get_db_connection()
cursor = conn.execute(...)
conn.close()  # May not be called if exception occurs

# WRONG - No cleanup on error
conn = get_db_connection()
try:
    # operations
    conn.commit()
finally:
    conn.close()  # Better, but use context manager instead
```

## Database Access Layers

### 1. ORM Layer (SQLAlchemy) - PREFERRED
- **Module**: `database_session.py`
- **Function**: `get_db_session()`
- **Use For**: All new code, complex queries, relationships
- **Benefits**: Type safety, relationship handling, automatic SQL generation

### 2. Raw SQL Layer (Legacy Support)
- **Module**: `db_config.py`
- **Function**: `get_db_connection()`
- **Use For**: Legacy code, simple queries, migrations
- **Note**: Gradually migrate to ORM

### 3. Direct Session (DEPRECATED)
- **DO NOT USE**: `SessionLocal()`, `scoped_session`
- These are internal to `database_session.py`

## Migration Path

### Current State (Mixed Patterns)
```python
# admin_ui.py - Raw connections
conn = get_db_connection()
cursor = conn.execute("SELECT * FROM tenants...")

# main.py - Mixed (some ORM, some raw)
with get_db_session() as session:
    principal = session.query(Principal)...
```

### Target State (Standardized ORM)
```python
# All files - Use ORM with context manager
with get_db_session() as session:
    tenant = session.query(Tenant).filter_by(tenant_id=tenant_id).first()
```

## Best Practices

### 1. Always Use Context Managers
```python
# ✅ GOOD - Automatic cleanup
with get_db_session() as session:
    # operations
    session.commit()

# ❌ BAD - Manual cleanup
session = SessionLocal()
# operations
session.close()
```

### 2. Explicit Commits
```python
with get_db_session() as session:
    tenant.name = "New Name"
    session.commit()  # Always explicit
```

### 3. Handle Rollbacks
```python
with get_db_session() as session:
    try:
        # multiple operations
        session.commit()
    except Exception as e:
        session.rollback()  # Automatic in context manager
        raise
```

### 4. Thread Safety
- `get_db_session()` uses `scoped_session` internally - thread-safe
- `get_db_connection()` creates new connection each time - thread-safe
- Never share sessions/connections between threads

## Database Configuration

### Environment Variables
```bash
# Option 1: DATABASE_URL (Preferred for production)
DATABASE_URL=postgresql://user:pass@localhost:5432/adcp

# Option 2: Individual variables
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=adcp
DB_USER=adcp_user
DB_PASSWORD=secure_password
```

### Connection Pooling
- SQLAlchemy handles connection pooling automatically
- Default pool size: 5 connections
- Max overflow: 10 connections
- Configure in `database_session.py` if needed

## Testing Patterns

### Unit Tests
```python
from unittest.mock import patch, MagicMock

@patch('database_session.get_db_session')
def test_function(mock_session):
    mock_session.return_value.__enter__.return_value = MagicMock()
    # test code
```

### Integration Tests
```python
def test_with_real_db():
    with get_db_session() as session:
        # Use test database
        tenant = Tenant(tenant_id='test', name='Test')
        session.add(tenant)
        session.commit()

        # Cleanup
        session.delete(tenant)
        session.commit()
```

## Common Issues and Solutions

### Issue: "current transaction is aborted"
**Cause**: PostgreSQL requires rollback after error
**Solution**: Use context manager (automatic rollback)

### Issue: Connection pool exhausted
**Cause**: Connections not being returned to pool
**Solution**: Always use context managers

### Issue: SQLite "database is locked"
**Cause**: Long-running transactions
**Solution**: Keep transactions short, use WAL mode

## Migration Examples from Issue #74

### Example 1: Simple SELECT Query Migration
**Before:**
```python
conn = get_db_connection()
cursor = conn.execute(
    "SELECT * FROM tenants WHERE tenant_id = ? AND is_active = ?",
    (tenant_id, True)
)
row = cursor.fetchone()
conn.close()
```

**After:**
```python
with get_db_session() as session:
    tenant = session.query(Tenant).filter_by(
        tenant_id=tenant_id,
        is_active=True
    ).first()
```

### Example 2: INSERT Operation Migration
**Before:**
```python
conn = get_db_connection()
conn.execute("""
    INSERT INTO tasks (tenant_id, task_id, task_type, status, details)
    VALUES (?, ?, ?, ?, ?)
""", (tenant_id, task_id, 'policy_review', 'pending', json.dumps(details)))
conn.connection.commit()
conn.close()
```

**After:**
```python
with get_db_session() as session:
    new_task = Task(
        tenant_id=tenant_id,
        task_id=task_id,
        task_type='policy_review',
        status='pending',
        details=details  # ORM handles JSON serialization
    )
    session.add(new_task)
    session.commit()
```

### Example 3: UPDATE Operation Migration
**Before:**
```python
conn = get_db_connection()
conn.execute("""
    UPDATE tasks SET status = ?, completed_at = ?
    WHERE task_id = ? AND tenant_id = ?
""", (status, datetime.now(), task_id, tenant_id))
conn.connection.commit()
conn.close()
```

**After:**
```python
with get_db_session() as session:
    task = session.query(Task).filter_by(
        task_id=task_id,
        tenant_id=tenant_id
    ).first()
    if task:
        task.status = status
        task.completed_at = datetime.now()
        session.commit()
```

## Gradual Migration Strategy

### Phase 1: Critical Path Endpoints (COMPLETED)
- Add context managers to high-traffic endpoints
- Fix connection leaks in error paths

### Phase 2: Standardize New Code
- All new code uses `get_db_session()`
- Document pattern in PR templates

### Phase 3: Migrate Legacy Code
- Convert `get_db_connection()` to `get_db_session()`
- Update one module at a time
- Maintain backwards compatibility

### Phase 4: Remove Legacy Layer
- Remove `get_db_connection()` function
- Update all imports
- Simplify database configuration

## Code Review Checklist

- [ ] Uses context manager (`with get_db_session()`)
- [ ] Explicit commits where needed
- [ ] No manual session/connection management
- [ ] Proper error handling (rollback handled)
- [ ] No shared sessions between requests/threads
- [ ] Follow ORM patterns for new code
