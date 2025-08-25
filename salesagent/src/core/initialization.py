"""Initialization and setup functions."""

import os
from rich.console import Console

from src.adapters.mock_creative_engine import MockCreativeEngine
from src.core.config_loader import load_config
from scripts.setup.init_database import init_db

# Initialize Rich console
console = Console()


def initialize_database():
    """Initialize the database if not in test mode."""
    # Only initialize DB if not in test mode
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        init_db()  # Tests will call with exit_on_error=False


def load_configuration():
    """Load configuration with fallback for test environments."""
    try:
        config = load_config()
    except RuntimeError as e:
        if "No tenant in context" in str(e):
            # Use minimal config for test environments
            config = {
                "creative_engine": {},
                "dry_run": False,
                "adapters": {"mock": {"enabled": True}},
                "ad_server": {"adapter": "mock", "enabled": True},
            }
        else:
            raise
    return config


def initialize_creative_engine():
    """Initialize creative engine with minimal config."""
    creative_engine_config = {}
    return MockCreativeEngine(creative_engine_config)


def load_media_buys_from_db():
    """Load existing media buys from database into memory on startup."""
    try:
        # We can't load tenant-specific media buys at startup since we don't have tenant context
        # Media buys will be loaded on-demand when needed
        console.print("[dim]Media buys will be loaded on-demand from database[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not initialize media buys from database: {e}[/yellow]")


# Initialize in-memory state
media_buys = {}
creative_assignments = {}
creative_statuses = {}

