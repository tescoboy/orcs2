"""Flask application factory for Admin UI."""

import logging
import os
import secrets

from flask import Flask, request
from flask_socketio import SocketIO, join_room

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, continue without it

from src.admin.blueprints.adapters import adapters_bp
from src.admin.blueprints.api import api_bp
from src.admin.blueprints.auth import auth_bp, init_oauth
from src.admin.blueprints.core import core_bp
from src.admin.blueprints.publisher import publisher_bp
from src.admin.blueprints.creatives import creatives_bp
from src.admin.blueprints.gam import gam_bp
from src.admin.blueprints.inventory import inventory_bp
from src.admin.blueprints.mcp_test import mcp_test_bp
from src.admin.blueprints.operations import operations_bp
from src.admin.blueprints.policy import policy_bp
from src.admin.blueprints.principals import principals_bp
from src.admin.blueprints.products import products_bp
from src.admin.blueprints.settings import settings_bp, superadmin_settings_bp
from src.admin.blueprints.tenants import tenants_bp
from src.admin.blueprints.users import users_bp
from src.admin.blueprints.admin_tenants import admin_tenants_bp
from src.admin.blueprints.admin_agents import admin_agents_bp
from src.admin.blueprints.agent_providers import agent_providers_bp
from src.admin.blueprints.mcp_management import mcp_management_bp
from src.api.buyer_orchestrator_router import buyer_orchestrator_bp
from src.api.performance_monitoring_router import performance_monitoring_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProxyFix:
    """Fix for proxy headers when running behind a reverse proxy."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Handle X-Forwarded-* headers
        scheme = environ.get("HTTP_X_FORWARDED_PROTO", "")
        host = environ.get("HTTP_X_FORWARDED_HOST", "")
        prefix = environ.get("HTTP_X_FORWARDED_PREFIX", "")

        if scheme:
            environ["wsgi.url_scheme"] = scheme
        if host:
            environ["HTTP_HOST"] = host
        if prefix:
            environ["SCRIPT_NAME"] = prefix

        return self.app(environ, start_response)


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="../../templates", static_folder="../../static")

    # Configuration
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
    app.logger.setLevel(logging.INFO)
    
    # Set database URL if not already set
    if not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:////Users/harvingupta/.adcp/adcp.db"
        logger.info(f"Set DATABASE_URL to: {os.environ['DATABASE_URL']}")
    else:
        logger.info(f"DATABASE_URL already set to: {os.environ.get('DATABASE_URL')}")

    # Apply any additional config
    if config:
        app.config.update(config)

    # Apply proxy fix
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Initialize OAuth
    init_oauth(app)

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
    app.socketio = socketio

    # Register blueprints
    app.register_blueprint(core_bp)  # Core routes (/, /health, /static, /mcp-test)
    app.register_blueprint(publisher_bp, url_prefix="/publisher")  # Publisher routes
    app.register_blueprint(auth_bp)  # No url_prefix - auth routes are at root
    app.register_blueprint(superadmin_settings_bp)  # Superadmin settings at /settings
    app.register_blueprint(admin_tenants_bp)  # Admin tenant management
    app.register_blueprint(admin_agents_bp)  # Admin agent management
    app.register_blueprint(agent_providers_bp)  # Agent provider endpoints
    app.register_blueprint(mcp_management_bp)  # MCP agent management
    app.register_blueprint(buyer_orchestrator_bp)  # Buyer orchestrator API
    app.register_blueprint(performance_monitoring_bp)  # Performance monitoring API
    app.register_blueprint(tenants_bp, url_prefix="/tenant")
    app.register_blueprint(products_bp, url_prefix="/tenant/<tenant_id>/products")
    app.register_blueprint(principals_bp, url_prefix="/tenant/<tenant_id>")
    app.register_blueprint(users_bp)  # Already has url_prefix in blueprint
    app.register_blueprint(gam_bp)
    app.register_blueprint(operations_bp, url_prefix="/tenant/<tenant_id>")
    app.register_blueprint(creatives_bp, url_prefix="/tenant/<tenant_id>/creative-formats")
    app.register_blueprint(policy_bp, url_prefix="/tenant/<tenant_id>/policy")
    app.register_blueprint(settings_bp, url_prefix="/tenant/<tenant_id>/settings")
    
    # Register AI settings blueprint
    try:
        from src.api.ai_settings_router import ai_settings_blueprint
        app.register_blueprint(ai_settings_blueprint)
    except ImportError:
        logger.warning("ai_settings_blueprint not found")
    
    # Register buyer UI blueprint
    try:
        import sys
        # Add the salesagent directory to the path so we can import from api
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from api.buyer_ui_router import buyer_ui_bp
        app.register_blueprint(buyer_ui_bp)
    except ImportError as e:
        logger.warning(f"buyer_ui_bp not found: {e}")
    
    # Register buyer campaign blueprint
    try:
        from api.buyer_campaign_router import buyer_campaign_bp
        app.register_blueprint(buyer_campaign_bp)
    except ImportError as e:
        logger.warning(f"buyer_campaign_bp not found: {e}")
    
    # Register buyer payload blueprint
    try:
        from api.buyer_payload_router import buyer_payload_bp
        app.register_blueprint(buyer_payload_bp)
    except ImportError as e:
        logger.warning(f"buyer_payload_bp not found: {e}")
    
    # Register health blueprint
    try:
        from api.health_router import health_bp
        app.register_blueprint(health_bp)
    except ImportError as e:
        logger.warning(f"health_bp not found: {e}")
    
    app.register_blueprint(adapters_bp, url_prefix="/tenant/<tenant_id>")
    app.register_blueprint(inventory_bp)  # Has its own internal routing
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(mcp_test_bp)

    # Import and register existing blueprints
    try:
        from src.admin.superadmin_api import superadmin_api

        app.register_blueprint(superadmin_api)
    except ImportError:
        logger.warning("superadmin_api blueprint not found")

    try:
        from src.admin.sync_api import sync_api

        app.register_blueprint(sync_api, url_prefix="/api/sync")
    except ImportError:
        logger.warning("sync_api blueprint not found")

    try:
        from src.adapters.gam_reporting_api import gam_reporting_api

        app.register_blueprint(gam_reporting_api)
    except ImportError:
        logger.warning("gam_reporting_api blueprint not found")

    # Register adapter-specific routes
    register_adapter_routes(app)

    # WebSocket handlers
    @socketio.on("connect")
    def handle_connect():
        """Handle WebSocket connection."""
        logger.info(f"Client connected: {request.sid}")

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle WebSocket disconnection."""
        logger.info(f"Client disconnected: {request.sid}")

    @socketio.on("subscribe")
    def handle_subscribe(data):
        """Handle subscription to tenant events."""
        tenant_id = data.get("tenant_id")
        if tenant_id:
            join_room(f"tenant_{tenant_id}")
            logger.info(f"Client {request.sid} subscribed to tenant {tenant_id}")

    return app, socketio


def register_adapter_routes(app):
    """Register adapter-specific configuration routes."""
    try:
        # Import adapter modules that have UI routes
        from src.adapters.google_ad_manager import GoogleAdManager
        from src.adapters.mock_ad_server import MockAdServer

        # Register routes for each adapter that supports UI routes
        # Note: We skip instantiation errors since routes are optional
        adapter_configs = [
            (GoogleAdManager, {"config": {}, "principal": None}),
            (MockAdServer, {"principal": None, "dry_run": False}),
        ]

        for adapter_class, kwargs in adapter_configs:
            try:
                # Try to create instance for route registration
                adapter_instance = adapter_class(**kwargs)
                if hasattr(adapter_instance, "register_ui_routes"):
                    adapter_instance.register_ui_routes(app)
                    logger.info(f"Registered UI routes for {adapter_class.__name__}")
            except Exception as e:
                # This is expected for some adapters that require specific config
                logger.debug(f"Could not register {adapter_class.__name__} routes: {e}")

    except Exception as e:
        logger.warning(f"Error importing adapter modules: {e}")


def broadcast_activity_to_websocket(tenant_id: str, activity: dict):
    """Broadcast activity to WebSocket clients."""
    try:
        from flask import current_app

        if hasattr(current_app, "socketio"):
            current_app.socketio.emit(
                "activity",
                activity,
                room=f"tenant_{tenant_id}",
                namespace="/",
            )
    except Exception as e:
        logger.error(f"Error broadcasting to WebSocket: {e}")


# Create the Flask app instance for CLI
app, socketio = create_app()
