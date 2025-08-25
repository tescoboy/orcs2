#!/usr/bin/env python3
"""Script to remove @require_tenant_access decorators from all blueprint files."""

import os
import re
from pathlib import Path

def remove_tenant_access_decorators(file_path):
    """Remove @require_tenant_access decorators from a file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove import statement
    content = re.sub(r'from src\.admin\.utils import require_tenant_access\n', '', content)
    content = re.sub(r'from src\.admin\.utils import [^,]*require_tenant_access[^,]*\n', '', content)
    content = re.sub(r'from src\.admin\.utils import [^,]*require_tenant_access[^,]*,\s*', 'from src.admin.utils import ', content)
    content = re.sub(r',\s*require_tenant_access[^,]*\n', '\n', content)
    
    # Remove @require_tenant_access() decorators
    content = re.sub(r'@require_tenant_access\([^)]*\)\n', '', content)
    
    # Fix function signatures that had tenant_id parameter
    # Pattern: def function_name(tenant_id, **kwargs):
    content = re.sub(r'def (\w+)\(tenant_id, \*\*kwargs\):', r'def \1():', content)
    content = re.sub(r'def (\w+)\(tenant_id, (\w+), \*\*kwargs\):', r'def \1(\2):', content)
    content = re.sub(r'def (\w+)\(tenant_id, (\w+), (\w+), \*\*kwargs\):', r'def \1(\2, \3):', content)
    
    # Remove tenant_id references in function bodies (simplify for demo)
    # This is a basic approach - in a real scenario you'd need more sophisticated handling
    content = re.sub(r'tenant_id=tenant_id', '', content)
    content = re.sub(r'filter_by\(tenant_id=tenant_id\)', 'filter_by()', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Processed: {file_path}")

def main():
    """Process all blueprint files."""
    blueprint_dir = Path("src/admin/blueprints")
    
    if not blueprint_dir.exists():
        print("Blueprint directory not found")
        return
    
    for py_file in blueprint_dir.glob("*.py"):
        if py_file.name != "__init__.py":
            remove_tenant_access_decorators(py_file)

if __name__ == "__main__":
    main()
