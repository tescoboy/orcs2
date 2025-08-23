"""Core environment checking functionality."""

import os
import sys
from pathlib import Path


def print_status(message, status="INFO"):
    """Print a status message with color coding."""
    colors = {
        "INFO": "\033[0;34m",    # Blue
        "SUCCESS": "\033[0;32m", # Green
        "WARNING": "\033[1;33m", # Yellow
        "ERROR": "\033[0;31m",   # Red
    }
    reset = "\033[0m"
    
    color = colors.get(status, colors["INFO"])
    print(f"{color}[{status}]{reset} {message}")


def check_env_file():
    """Check if .env file exists and load it."""
    env_file = Path(".env")
    if env_file.exists():
        print_status(".env file found", "SUCCESS")
        
        # Load environment variables from .env
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        
        return True
    else:
        print_status("No .env file found", "WARNING")
        print_status("Create .env file with required environment variables")
        return False


def check_gemini_api_key():
    """Check if GEMINI_API_KEY is set."""
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if gemini_key:
        print_status("GEMINI_API_KEY is set", "SUCCESS")
        return True
    else:
        print_status("GEMINI_API_KEY not found", "WARNING")
        print_status("AI features (product ranking, prompt configuration) will not work")
        print_status("Add to .env: GEMINI_API_KEY=your_key_here")
        return False


def check_database_url():
    """Check DATABASE_URL configuration."""
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        print_status(f"DATABASE_URL is set: {db_url}", "SUCCESS")
        return True
    else:
        # Default to SQLite
        default_db = "sqlite:///./orcs2.db"
        print_status("DATABASE_URL not set, using default SQLite", "INFO")
        print_status(f"Database will be created at: {default_db}")
        print_status("Add to .env: DATABASE_URL=sqlite:///./orcs2.db")
        return True


def check_python_version():
    """Check Python version."""
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print_status(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - OK", "SUCCESS")
        return True
    else:
        print_status(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - Requires Python 3.8+", "ERROR")
        return False


def check_virtual_environment():
    """Check virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_status("Virtual environment active", "SUCCESS")
        return True
    else:
        print_status("No virtual environment detected", "WARNING")
        print_status("Consider using a virtual environment: python3 -m venv venv")
        return False


def check_dependencies():
    """Check Python dependencies."""
    required_packages = ['flask', 'sqlalchemy', 'pytest']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print_status(f"{package} - OK", "SUCCESS")
        except ImportError:
            missing_packages.append(package)
            print_status(f"{package} - Missing", "WARNING")
    
    if missing_packages:
        print_status(f"Install missing packages: pip install {' '.join(missing_packages)}", "WARNING")
        return False
    
    return True


def check_repo_indicators():
    """Check for repository indicator files."""
    repo_indicators = ['package.json', 'pyproject.toml', 'requirements.txt', 'src']
    found_indicators = [indicator for indicator in repo_indicators if Path(indicator).exists()]
    return found_indicators
