"""Core application routes blueprint."""

import json
import logging
import os
import secrets
import string
from datetime import UTC, datetime

from flask import Blueprint, flash, redirect, render_template, request, send_from_directory, session, url_for
from sqlalchemy import text

from src.admin.utils import require_auth
from src.core.database.database_session import get_db_session
from src.core.database.models import Principal, Tenant, Product

logger = logging.getLogger(__name__)

# Create blueprint
core_bp = Blueprint("core", __name__)


@core_bp.route("/")
def index():
    """Main index page - redirects to demo home for easy access."""
    return redirect(url_for("core.demo_home"))


@core_bp.route("/health")
def health():
    """Health check endpoint."""
    try:
        with get_db_session() as db_session:
            db_session.execute(text("SELECT 1"))
            return "OK", 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return f"Database connection failed: {str(e)}", 500


@core_bp.route("/create_publisher", methods=["GET", "POST"])
def create_publisher_simple():
    """Create a new publisher without authentication (for demo)."""
    if request.method == "GET":
        return render_template("create_tenant.html")


@core_bp.route("/select_publisher", methods=["GET", "POST"])
def select_publisher():
    """Simple publisher selector page."""
    if request.method == "GET":
        # Get all tenants using the same database session as other routes
        try:
            with get_db_session() as db_session:
                tenants = db_session.query(Tenant).order_by(Tenant.name).all()
            return render_template("simple_tenant_selector.html", tenants=tenants)
        except Exception as e:
            logger.error(f"Error loading tenants for select_publisher: {e}", exc_info=True)
            return f"Error loading tenants: {str(e)}", 500
    
    # Handle POST - redirect to selected publisher
    tenant_id = request.form.get("tenant_id")
    if tenant_id:
        return redirect(f"/publisher/{tenant_id}/products")
    else:
        return redirect("/select_publisher")


@core_bp.route("/demo")
def demo_home():
    """Demo home page - freely accessible without authentication."""
    try:
        with get_db_session() as db_session:
            tenants = db_session.query(Tenant).order_by(Tenant.name).all()
            tenant_list = []
            for tenant in tenants:
                tenant_list.append({
                    "tenant_id": tenant.tenant_id,
                    "name": tenant.name,
                    "subdomain": tenant.subdomain,
                    "is_active": tenant.is_active,
                    "created_at": tenant.created_at,
                })
        return render_template("demo_home.html", tenants=tenant_list)
    except Exception as e:
        logger.error(f"Error loading demo home: {e}", exc_info=True)
        return f"Error loading demo: {str(e)}", 500


@core_bp.route("/demo/tenant/<tenant_id>")
def demo_tenant_switch(tenant_id):
    """Switch to a specific tenant in demo mode."""
    try:
        with get_db_session() as db_session:
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if not tenant:
                return "Tenant not found", 404
            
            # Set session data for demo mode
            session["demo_tenant_id"] = tenant_id
            session["demo_tenant_name"] = tenant.name
            session["demo_mode"] = True
            
            # Call the dashboard function directly to avoid redirect issues
            from src.admin.blueprints.tenants import dashboard
            return dashboard(tenant_id)
    except Exception as e:
        logger.error(f"Error switching to tenant: {e}", exc_info=True)
        return f"Error switching tenant: {str(e)}", 500






    # Handle POST request
    try:
        # Get form data
        tenant_name = request.form.get("name", "").strip()
        subdomain = request.form.get("subdomain", "").strip()
        ad_server = request.form.get("ad_server", "mock").strip()

        if not tenant_name:
            flash("Publisher name is required", "error")
            return render_template("create_tenant.html")

        # Generate tenant ID if not provided
        if not subdomain:
            subdomain = tenant_name.lower().replace(" ", "_").replace("-", "_")
            # Remove non-alphanumeric characters
            subdomain = "".join(c for c in subdomain if c.isalnum() or c == "_")

        tenant_id = f"tenant_{subdomain}"

        # Generate admin token
        admin_token = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

        with get_db_session() as db_session:
            # Check if tenant already exists
            existing = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if existing:
                flash(f"Publisher with ID {tenant_id} already exists", "error")
                return render_template("create_tenant.html")

            # Create new tenant
            new_tenant = Tenant(
                tenant_id=tenant_id,
                name=tenant_name,
                subdomain=subdomain,
                is_active=True,
                ad_server=ad_server,
                admin_token=admin_token,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )

            db_session.add(new_tenant)
            db_session.commit()

            flash(f"Publisher '{tenant_name}' created successfully!", "success")
            
            # Show success page with access info
            return render_template("create_tenant.html", 
                                 success=True,
                                 tenant_name=tenant_name,
                                 tenant_id=tenant_id,
                                 admin_token=admin_token,
                                 login_url=f"/tenant/{tenant_id}/login")

    except Exception as e:
        logger.error(f"Error creating publisher: {e}")
        flash(f"Error creating publisher: {str(e)}", "error")
        return render_template("create_tenant.html")


@core_bp.route("/create_tenant", methods=["GET", "POST"])
@require_auth(admin_only=True)
def create_tenant():
    """Create a new tenant."""
    if request.method == "GET":
        return render_template("create_tenant.html")

    # Handle POST request
    try:
        # Get form data
        tenant_name = request.form.get("name", "").strip()
        subdomain = request.form.get("subdomain", "").strip()
        ad_server = request.form.get("ad_server", "mock").strip()

        if not tenant_name:
            flash("Tenant name is required", "error")
            return render_template("create_tenant.html")

        # Generate tenant ID if not provided
        if not subdomain:
            subdomain = tenant_name.lower().replace(" ", "_").replace("-", "_")
            # Remove non-alphanumeric characters
            subdomain = "".join(c for c in subdomain if c.isalnum() or c == "_")

        tenant_id = f"tenant_{subdomain}"

        # Generate admin token
        admin_token = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

        with get_db_session() as db_session:
            # Check if tenant already exists
            existing = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if existing:
                flash(f"Tenant with ID {tenant_id} already exists", "error")
                return render_template("create_tenant.html")

            # Create new tenant
            new_tenant = Tenant(
                tenant_id=tenant_id,
                name=tenant_name,
                subdomain=subdomain,
                is_active=True,
                ad_server=ad_server,
                admin_token=admin_token,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Set default configuration based on ad server
            if ad_server == "google_ad_manager":
                # GAM requires additional configuration
                new_tenant.gam_network_code = request.form.get("gam_network_code", "")
                new_tenant.gam_refresh_token = request.form.get("gam_refresh_token", "")

            # Set feature flags
            new_tenant.max_daily_budget = float(request.form.get("max_daily_budget", "10000"))
            new_tenant.enable_aee_signals = "enable_aee_signals" in request.form
            new_tenant.human_review_required = "human_review_required" in request.form

            # Set authorization settings
            authorized_emails = request.form.get("authorized_emails", "")
            if authorized_emails:
                new_tenant.authorized_emails = json.dumps(
                    [e.strip() for e in authorized_emails.split(",") if e.strip()]
                )

            authorized_domains = request.form.get("authorized_domains", "")
            if authorized_domains:
                new_tenant.authorized_domains = json.dumps(
                    [d.strip() for d in authorized_domains.split(",") if d.strip()]
                )

            db_session.add(new_tenant)

            # Create default principal for the tenant
            default_principal = Principal(
                tenant_id=tenant_id,
                principal_id=f"{tenant_id}_default",
                name=f"{tenant_name} Default Principal",
                access_token=admin_token,  # Use same token for simplicity
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            db_session.add(default_principal)

            db_session.commit()

            flash(f"Tenant '{tenant_name}' created successfully!", "success")
            return redirect(url_for("tenants.dashboard", tenant_id=tenant_id))

    except Exception as e:
        logger.error(f"Error creating tenant: {e}", exc_info=True)
        flash(f"Error creating tenant: {str(e)}", "error")
        return render_template("create_tenant.html")


@core_bp.route("/static/<path:path>")
def send_static(path):
    """Serve static files."""
    return send_from_directory("static", path)


@core_bp.route("/mcp-test")
@require_auth(admin_only=True)
def mcp_test():
    """MCP protocol testing interface for super admins."""
    # Get all tenants and their principals
    with get_db_session() as db_session:
        # Get tenants
        tenant_objs = db_session.query(Tenant).filter_by(is_active=True).order_by(Tenant.name).all()
        tenants = []
        for tenant in tenant_objs:
            tenants.append(
                {
                    "tenant_id": tenant.tenant_id,
                    "name": tenant.name,
                    "subdomain": tenant.subdomain,
                }
            )

        # Get all principals with their tenant info
        principal_objs = (
            db_session.query(Principal)
            .join(Tenant)
            .filter(Tenant.is_active)
            .order_by(Tenant.name, Principal.name)
            .all()
        )
        principals = []
        for principal in principal_objs:
            # Get the tenant name via relationship or separate query
            tenant_name = db_session.query(Tenant.name).filter_by(tenant_id=principal.tenant_id).scalar()
            principals.append(
                {
                    "principal_id": principal.principal_id,
                    "name": principal.name,
                    "tenant_id": principal.tenant_id,
                    "access_token": principal.access_token,
                    "tenant_name": tenant_name,
                }
            )

    # Get server URL - use correct port from environment
    server_port = int(os.environ.get("ADCP_SALES_PORT", 8005))
    server_url = f"http://localhost:{server_port}/mcp/"

    return render_template("mcp_test.html", tenants=tenants, principals=principals, server_url=server_url)
