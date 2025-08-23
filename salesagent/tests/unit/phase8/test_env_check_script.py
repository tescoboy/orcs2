"""Test environment check script functionality."""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path
from unittest.mock import patch


class TestEnvCheckScript:
    """Test the environment check script."""
    
    def test_script_runs_without_gemini_key(self):
        """Test script runs and warns about missing GEMINI_API_KEY."""
        script_path = Path(__file__).parent.parent.parent.parent / 'scripts' / 'check_env.py'
        
        # Create temporary environment without GEMINI_API_KEY
        env = os.environ.copy()
        if 'GEMINI_API_KEY' in env:
            del env['GEMINI_API_KEY']
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Script should exit with 0 (not block development)
        assert result.returncode == 0
        
        # Should warn about missing GEMINI_API_KEY
        assert 'GEMINI_API_KEY not found' in result.stdout
        assert 'WARNING' in result.stdout
    
    def test_script_runs_with_gemini_key(self):
        """Test script runs successfully with GEMINI_API_KEY set."""
        script_path = Path(__file__).parent.parent.parent.parent / 'scripts' / 'check_env.py'
        
        # Create environment with GEMINI_API_KEY
        env = os.environ.copy()
        env['GEMINI_API_KEY'] = 'test-key-123'
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Script should exit with 0
        assert result.returncode == 0
        
        # Should show success for GEMINI_API_KEY
        assert 'GEMINI_API_KEY is set' in result.stdout
        assert 'SUCCESS' in result.stdout
    
    def test_script_checks_python_environment(self):
        """Test script checks Python environment."""
        script_path = Path(__file__).parent.parent.parent.parent / 'scripts' / 'check_env.py'
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        assert result.returncode == 0
        
        # Should check Python version
        assert 'Python' in result.stdout
        assert 'OK' in result.stdout or 'WARNING' in result.stdout
    
    def test_script_checks_working_directory(self):
        """Test script checks working directory."""
        script_path = Path(__file__).parent.parent.parent.parent / 'scripts' / 'check_env.py'
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        assert result.returncode == 0
        
        # Should check working directory
        assert 'Working directory' in result.stdout
    
    def test_script_checks_dependencies(self):
        """Test script checks Python dependencies."""
        script_path = Path(__file__).parent.parent.parent.parent / 'scripts' / 'check_env.py'
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        assert result.returncode == 0
        
        # Should check for key dependencies
        assert 'flask' in result.stdout or 'sqlalchemy' in result.stdout or 'pytest' in result.stdout
    
    def test_script_handles_missing_env_file(self):
        """Test script handles missing .env file gracefully."""
        script_path = Path(__file__).parent.parent.parent.parent / 'scripts' / 'check_env.py'
        
        # Create temporary directory without .env file
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=temp_dir
            )
            
            # Script should still exit with 0
            assert result.returncode == 0
            
            # Should warn about missing .env file
            assert 'No .env file found' in result.stdout
            assert 'WARNING' in result.stdout
    
    def test_script_loads_env_file(self):
        """Test script loads environment variables from .env file."""
        script_path = Path(__file__).parent.parent.parent.parent / 'scripts' / 'check_env.py'
        
        # Create temporary directory with .env file
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / '.env'
            env_file.write_text('GEMINI_API_KEY=test-key-from-file\nDATABASE_URL=sqlite:///test.db')
            
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=temp_dir
            )
            
            assert result.returncode == 0
            
            # Should find and load .env file
            assert '.env file found' in result.stdout
            assert 'SUCCESS' in result.stdout
    
    def test_script_always_exits_zero(self):
        """Test script always exits with code 0 to not block development."""
        script_path = Path(__file__).parent.parent.parent.parent / 'scripts' / 'check_env.py'
        
        # Test with various conditions
        test_cases = [
            {},  # No environment variables
            {'GEMINI_API_KEY': 'test-key'},  # With GEMINI_API_KEY
            {'DATABASE_URL': 'sqlite:///test.db'},  # With DATABASE_URL
        ]
        
        for env_vars in test_cases:
            env = os.environ.copy()
            env.update(env_vars)
            
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent
            )
            
            # Script should always exit with 0
            assert result.returncode == 0, f"Script failed with env vars: {env_vars}"
    
    def test_script_provides_helpful_messages(self):
        """Test script provides helpful messages for common issues."""
        script_path = Path(__file__).parent.parent.parent.parent / 'scripts' / 'check_env.py'
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        assert result.returncode == 0
        
        # Should provide helpful messages
        output = result.stdout
        assert any(keyword in output for keyword in [
            'Add to .env',
            'Create .env file',
            'Install missing packages',
            'Consider using a virtual environment'
        ])


# Import sys for subprocess calls
import sys
