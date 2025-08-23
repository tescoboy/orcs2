"""Test file length constraints."""

import os
import pytest
from pathlib import Path


class TestFileLengths:
    """Test that all files adhere to the 150-line limit."""
    
    def test_python_files_under_150_lines(self):
        """Test that all Python files are under 150 lines."""
        repo_root = Path(__file__).parent.parent.parent.parent
        python_files = []
        
        # Walk through the repository
        for root, dirs, files in os.walk(repo_root):
            # Skip virtual environments and third-party directories
            if any(skip in root for skip in ['venv', '.venv', '__pycache__', '.git', 'node_modules']):
                continue
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    python_files.append(file_path)
        
        # Check each Python file
        oversized_files = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = len(f.readlines())
                
                if line_count > 150:
                    relative_path = file_path.relative_to(repo_root)
                    oversized_files.append(f"{relative_path}: {line_count} lines")
            
            except Exception as e:
                # Skip files that can't be read (binary, etc.)
                continue
        
        if oversized_files:
            error_msg = "The following Python files exceed 150 lines:\n"
            error_msg += "\n".join(oversized_files)
            error_msg += "\n\nPlease split these files to adhere to the 150-line limit."
            pytest.fail(error_msg)
    
    def test_html_template_files_under_150_lines(self):
        """Test that all HTML template files are under 150 lines."""
        repo_root = Path(__file__).parent.parent.parent.parent
        html_files = []
        
        # Walk through the repository
        for root, dirs, files in os.walk(repo_root):
            # Skip virtual environments and third-party directories
            if any(skip in root for skip in ['venv', '.venv', '__pycache__', '.git', 'node_modules']):
                continue
            
            for file in files:
                if file.endswith('.html'):
                    file_path = Path(root) / file
                    html_files.append(file_path)
        
        # Check each HTML file
        oversized_files = []
        for file_path in html_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = len(f.readlines())
                
                if line_count > 150:
                    relative_path = file_path.relative_to(repo_root)
                    oversized_files.append(f"{relative_path}: {line_count} lines")
            
            except Exception as e:
                # Skip files that can't be read
                continue
        
        if oversized_files:
            error_msg = "The following HTML template files exceed 150 lines:\n"
            error_msg += "\n".join(oversized_files)
            error_msg += "\n\nPlease split these files to adhere to the 150-line limit."
            pytest.fail(error_msg)
    
    def test_shell_scripts_under_150_lines(self):
        """Test that all shell scripts are under 150 lines."""
        repo_root = Path(__file__).parent.parent.parent.parent
        shell_files = []
        
        # Walk through the repository
        for root, dirs, files in os.walk(repo_root):
            # Skip virtual environments and third-party directories
            if any(skip in root for skip in ['venv', '.venv', '__pycache__', '.git', 'node_modules']):
                continue
            
            for file in files:
                if file.endswith(('.sh', '.bash')):
                    file_path = Path(root) / file
                    shell_files.append(file_path)
        
        # Check each shell file
        oversized_files = []
        for file_path in shell_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = len(f.readlines())
                
                if line_count > 150:
                    relative_path = file_path.relative_to(repo_root)
                    oversized_files.append(f"{relative_path}: {line_count} lines")
            
            except Exception as e:
                # Skip files that can't be read
                continue
        
        if oversized_files:
            error_msg = "The following shell script files exceed 150 lines:\n"
            error_msg += "\n".join(oversized_files)
            error_msg += "\n\nPlease split these files to adhere to the 150-line limit."
            pytest.fail(error_msg)
    
    def test_makefile_under_150_lines(self):
        """Test that Makefile is under 150 lines."""
        repo_root = Path(__file__).parent.parent.parent.parent
        makefile_path = repo_root / 'Makefile'
        
        if makefile_path.exists():
            try:
                with open(makefile_path, 'r', encoding='utf-8') as f:
                    line_count = len(f.readlines())
                
                if line_count > 150:
                    pytest.fail(f"Makefile exceeds 150 lines: {line_count} lines")
            except Exception as e:
                pytest.fail(f"Could not read Makefile: {e}")
    
    def test_phase_specific_files_under_150_lines(self):
        """Test that Phase 7 and 8 files are under 150 lines."""
        repo_root = Path(__file__).parent.parent.parent.parent
        
        # Phase 7 files
        phase7_files = [
            'services/ad_payload_core.py',
            'services/ad_payload_mapper.py',
            'api/buyer_payload_router.py',
            'templates/ui/buyer/payload_view.html',
            'templates/ui/buyer/_payload_view_content.html',
            'templates/ui/buyer/payload_error.html'
        ]
        
        # Phase 8 files
        phase8_files = [
            'api/health_router.py',
            'scripts/dev_server.sh',
            'scripts/check_env.py',
            'Makefile',
            'README_DEV.md'
        ]
        
        all_files = phase7_files + phase8_files
        oversized_files = []
        
        for file_path in all_files:
            full_path = repo_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        line_count = len(f.readlines())
                    
                    if line_count > 150:
                        oversized_files.append(f"{file_path}: {line_count} lines")
                
                except Exception as e:
                    # Skip files that can't be read
                    continue
        
        if oversized_files:
            error_msg = "The following Phase 7/8 files exceed 150 lines:\n"
            error_msg += "\n".join(oversized_files)
            error_msg += "\n\nPlease split these files to adhere to the 150-line limit."
            pytest.fail(error_msg)
