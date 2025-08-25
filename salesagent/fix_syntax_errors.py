#!/usr/bin/env python3
"""Script to fix syntax errors caused by decorator removal."""

import os
import re
from pathlib import Path

def fix_syntax_errors(file_path):
    """Fix syntax errors in a file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix dangling commas in function calls
    content = re.sub(r'\(\s*,\s*', '(', content)
    content = re.sub(r',\s*\)', ')', content)
    
    # Fix filter_by() calls that are empty
    content = re.sub(r'\.filter_by\(\)', '', content)
    
    # Fix render_template calls with dangling commas
    content = re.sub(r'render_template\([^)]*,\s*,', 'render_template(', content)
    content = re.sub(r',\s*,([^,]*\))', r',\1', content)
    
    # Fix url_for calls with dangling commas
    content = re.sub(r'url_for\([^)]*,\s*\)', 'url_for()', content)
    
    # Fix Tenant() and Principal() constructors with dangling commas
    content = re.sub(r'Tenant\(\s*,\s*', 'Tenant(', content)
    content = re.sub(r'Principal\(\s*,\s*', 'Principal(', content)
    
    # Fix filter_by calls with dangling commas
    content = re.sub(r'\.filter_by\([^)]*,\s*,', '.filter_by(', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed: {file_path}")

def main():
    """Process all blueprint files."""
    blueprint_dir = Path("src/admin/blueprints")
    
    if not blueprint_dir.exists():
        print("Blueprint directory not found")
        return
    
    for py_file in blueprint_dir.glob("*.py"):
        if py_file.name != "__init__.py":
            fix_syntax_errors(py_file)

if __name__ == "__main__":
    main()
