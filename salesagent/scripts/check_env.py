#!/usr/bin/env python3
"""Environment check script for orcs2-salesagent."""

import os
import sys
from pathlib import Path

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from check_env_core import (
    print_status, check_env_file, check_gemini_api_key, check_database_url,
    check_python_version, check_virtual_environment, check_dependencies,
    check_repo_indicators
)


def check_working_directory():
    """Check if we're in the correct working directory."""
    current_dir = Path.cwd()
    found_indicators = check_repo_indicators()
    
    if found_indicators:
        print_status(f"Working directory OK: {current_dir}", "SUCCESS")
        print_status(f"Found indicators: {', '.join(found_indicators)}", "INFO")
        return True
    else:
        print_status("Working directory may not be repository root", "WARNING")
        print_status("Make sure you're in the orcs2-salesagent directory")
        return False


def check_python_environment():
    """Check Python environment and dependencies."""
    print_status("Checking Python environment...")
    
    version_ok = check_python_version()
    venv_ok = check_virtual_environment()
    deps_ok = check_dependencies()
    
    return version_ok and deps_ok


def main():
    """Main environment check function."""
    print_status("orcs2-salesagent Environment Check", "INFO")
    print_status("=" * 50)
    
    checks = [
        check_working_directory,
        check_python_environment,
        check_env_file,
        check_gemini_api_key,
        check_database_url,
    ]
    
    all_passed = True
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print_status(f"Check failed with error: {e}", "ERROR")
            all_passed = False
        print()
    
    if all_passed:
        print_status("Environment check completed successfully!", "SUCCESS")
        print_status("You can now run: make dev")
    else:
        print_status("Environment check completed with warnings", "WARNING")
        print_status("Please address the issues above before starting development")
    
    # Always exit with 0 to not block development
    sys.exit(0)


if __name__ == "__main__":
    main()
