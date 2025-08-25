"""Admin tenant management blueprint for comprehensive CRUD operations."""

import json
import logging
import secrets
import string
import uuid
from datetime import UTC, datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

# from src.admin.utils import require_auth  # Removed for demo mode
from src.core.database.database_session import get_db_session
from src.core.database.models import Principal, Tenant
from src.services.agent_management_service import agent_management_service

logger = logging.getLogger(__name__)

# Create Blueprint
admin_tenants_bp = Blueprint("admin_tenants", __name__, url_prefix="/admin")


@admin_tenants_bp.route("/tenants")
def list_tenants():
    """List all tenants with admin interface."""
    try:
        with get_db_session() as db_session:
            tenants = db_session.query(Tenant).order_by(Tenant.created_at.desc()).all()
            
            tenant_list = []
            for tenant in tenants:
                # Get principals count
                principals_count = db_session.query(Principal).filter_by(tenant_id=tenant.tenant_id).count()
                
                tenant_list.append({
                    "tenant_id": tenant.tenant_id,
                    "name": tenant.name,
                    "subdomain": tenant.subdomain,
                    "is_active": tenant.is_active,
                    "ad_server": tenant.ad_server,
                    "billing_plan": tenant.billing_plan,
                    "max_daily_budget": tenant.max_daily_budget,
                    "principals_count": principals_count,
                    "created_at": tenant.created_at,
                    "updated_at": tenant.updated_at,
                })
            
            return render_template("admin/tenants/list.html", tenants=tenant_list)
            
    except Exception as e:
        logger.error(f"Error loading tenants: {e}", exc_info=True)
        flash("Error loading tenants", "error")
        return redirect(url_for("core.index"))


@admin_tenants_bp.route("/tenants/create", methods=["GET", "POST"])
def create_tenant():
    """Create a new tenant."""
    if request.method == "GET":
        return render_template("admin/tenants/create.html")
    
    try:
        # Get form data
        tenant_name = request.form.get("name", "").strip()
        subdomain = request.form.get("subdomain", "").strip()
        ad_server = request.form.get("ad_server", "mock").strip()
        billing_plan = request.form.get("billing_plan", "standard").strip()
        max_daily_budget = float(request.form.get("max_daily_budget", "10000"))
        enable_aee_signals = "enable_aee_signals" in request.form
        human_review_required = "human_review_required" in request.form
        
        if not tenant_name:
            flash("Tenant name is required", "error")
            return render_template("admin/tenants/create.html")
        
        # Generate tenant ID if not provided
        if not subdomain:
            subdomain = tenant_name.lower().replace(" ", "_").replace("-", "_")
            subdomain = "".join(c for c in subdomain if c.isalnum() or c == "_")
        
        tenant_id = f"tenant_{subdomain}"
        
        # Generate admin token
        admin_token = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        with get_db_session() as db_session:
            # Check if tenant already exists
            existing = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if existing:
                flash(f"Tenant with ID {tenant_id} already exists", "error")
                return render_template("admin/tenants/create.html")
            
            # Create new tenant
            new_tenant = Tenant(
                tenant_id=tenant_id,
                name=tenant_name,
                subdomain=subdomain,
                is_active=True,
                ad_server=ad_server,
                billing_plan=billing_plan,
                max_daily_budget=max_daily_budget,
                enable_aee_signals=enable_aee_signals,
                human_review_required=human_review_required,
                admin_token=admin_token,
                authorized_emails=json.dumps([]),
                authorized_domains=json.dumps([]),
                auto_approve_formats=json.dumps(["display_300x250"]),
                policy_settings=json.dumps({}),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            
            db_session.add(new_tenant)
            
            # Create default principal with mock platform mapping
            default_platform_mapping = {
                "mock": {
                    "advertiser_id": f"mock_{tenant_id}",
                    "advertiser_name": f"{tenant_name} Mock Advertiser"
                }
            }
            
            default_principal = Principal(
                tenant_id=tenant_id,
                principal_id=f"{tenant_id}_default",
                name=f"{tenant_name} Default Principal",
                access_token=admin_token,
                platform_mappings=json.dumps(default_platform_mapping),
            )
            db_session.add(default_principal)
            
            db_session.commit()
            
            # Create default agents for the new tenant
            try:
                default_agents = agent_management_service.create_default_agents_for_tenant(tenant_id)
                if default_agents:
                    logger.info(f"Created {len(default_agents)} default agents for tenant {tenant_id}")
                else:
                    logger.warning(f"No default agents created for tenant {tenant_id}")
            except Exception as agent_error:
                logger.error(f"Error creating default agents for tenant {tenant_id}: {agent_error}")
                # Don't fail tenant creation if agent creation fails
            
            flash(f"Tenant '{tenant_name}' created successfully!", "success")
            return redirect(url_for("admin_tenants.list_tenants"))
            
    except Exception as e:
        logger.error(f"Error creating tenant: {e}", exc_info=True)
        flash(f"Error creating tenant: {str(e)}", "error")
        return render_template("admin/tenants/create.html")


@admin_tenants_bp.route("/tenants/<tenant_id>")
def view_tenant(tenant_id):
    """View tenant details."""
    try:
        with get_db_session() as db_session:
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if not tenant:
                flash("Tenant not found", "error")
                return redirect(url_for("admin_tenants.list_tenants"))
            
            # Get principals
            principals = db_session.query(Principal).filter_by(tenant_id=tenant_id).all()
            
            return render_template("admin/tenants/view.html", tenant=tenant, principals=principals)
            
    except Exception as e:
        logger.error(f"Error loading tenant: {e}", exc_info=True)
        flash("Error loading tenant", "error")
        return redirect(url_for("admin_tenants.list_tenants"))


@admin_tenants_bp.route("/tenants/<tenant_id>/edit", methods=["GET", "POST"])
def edit_tenant(tenant_id):
    """Edit tenant details."""
    try:
        with get_db_session() as db_session:
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if not tenant:
                flash("Tenant not found", "error")
                return redirect(url_for("admin_tenants.list_tenants"))
            
            if request.method == "GET":
                return render_template("admin/tenants/edit.html", tenant=tenant)
            
            # Handle POST request
            tenant.name = request.form.get("name", tenant.name).strip()
            tenant.subdomain = request.form.get("subdomain", tenant.subdomain).strip()
            tenant.ad_server = request.form.get("ad_server", tenant.ad_server).strip()
            tenant.billing_plan = request.form.get("billing_plan", tenant.billing_plan).strip()
            tenant.max_daily_budget = float(request.form.get("max_daily_budget", tenant.max_daily_budget))
            tenant.enable_aee_signals = "enable_aee_signals" in request.form
            tenant.human_review_required = "human_review_required" in request.form
            tenant.updated_at = datetime.now(UTC)
            
            db_session.commit()
            
            flash(f"Tenant '{tenant.name}' updated successfully!", "success")
            return redirect(url_for("admin_tenants.view_tenant", tenant_id=tenant_id))
            
    except Exception as e:
        logger.error(f"Error updating tenant: {e}", exc_info=True)
        flash(f"Error updating tenant: {str(e)}", "error")
        return redirect(url_for("admin_tenants.list_tenants"))


@admin_tenants_bp.route("/tenants/<tenant_id>/toggle", methods=["POST"])
def toggle_tenant(tenant_id):
    """Toggle tenant active status."""
    try:
        with get_db_session() as db_session:
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if not tenant:
                return jsonify({"error": "Tenant not found"}), 404
            
            tenant.is_active = not tenant.is_active
            tenant.updated_at = datetime.now(UTC)
            db_session.commit()
            
            status = "activated" if tenant.is_active else "deactivated"
            return jsonify({
                "success": True,
                "message": f"Tenant {status} successfully",
                "is_active": tenant.is_active
            })
            
    except Exception as e:
        logger.error(f"Error toggling tenant: {e}", exc_info=True)
        return jsonify({"error": "Error updating tenant"}), 500


@admin_tenants_bp.route("/tenants/<tenant_id>/delete", methods=["POST"])
def delete_tenant(tenant_id):
    """Delete tenant (soft delete)."""
    try:
        with get_db_session() as db_session:
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if not tenant:
                flash("Tenant not found", "error")
                return redirect(url_for("admin_tenants.list_tenants"))
            
            # Soft delete by setting is_active to False
            tenant.is_active = False
            tenant.updated_at = datetime.now(UTC)
            db_session.commit()
            
            flash(f"Tenant '{tenant.name}' deactivated successfully!", "success")
            return redirect(url_for("admin_tenants.list_tenants"))
            
    except Exception as e:
        logger.error(f"Error deleting tenant: {e}", exc_info=True)
        flash(f"Error deleting tenant: {str(e)}", "error")
        return redirect(url_for("admin_tenants.list_tenants"))


@admin_tenants_bp.route("/tenants/<tenant_id>/regenerate_token", methods=["POST"])
def regenerate_token(tenant_id):
    """Regenerate admin token for tenant."""
    try:
        with get_db_session() as db_session:
            tenant = db_session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            if not tenant:
                return jsonify({"error": "Tenant not found"}), 404
            
            # Generate new admin token
            new_token = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
            tenant.admin_token = new_token
            tenant.updated_at = datetime.now(UTC)
            db_session.commit()
            
            return jsonify({
                "success": True,
                "message": "Admin token regenerated successfully",
                "new_token": new_token
            })
            
    except Exception as e:
        logger.error(f"Error regenerating token: {e}", exc_info=True)
        return jsonify({"error": "Error regenerating token"}), 500
