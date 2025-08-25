"""Principals (Advertisers) management blueprint for admin UI."""

import json
import logging
import secrets
import uuid
from datetime import UTC, datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from src.core.database.database_session import get_db_session
from src.core.database.models import MediaBuy, Principal, Tenant

logger = logging.getLogger(__name__)

# Create Blueprint
principals_bp = Blueprint("principals", __name__, url_prefix="/tenant/<tenant_id>")


@principals_bp.route("/principals")
def list_principals(tenant_id):
    """List all principals (advertisers) for a tenant."""
    try:
        with get_db_session() as db_session:
            tenant = db_session.query(Tenant).first()
            if not tenant:
                flash("Tenant not found", "error")
                return redirect(url_for("core.index"))

            principals = db_session.query(Principal).order_by(Principal.name).all()

            # Convert to dict format for template
            principals_list = []
            for principal in principals:
                # Count media buys for this principal
                media_buy_count = (
                    db_session.query(MediaBuy)
                    .filter_by(principal_id=principal.principal_id)
                    .count()
                )

                principal_dict = {
                    "principal_id": principal.principal_id,
                    "name": principal.name,
                    "access_token": principal.access_token,
                    "platform_mappings": json.loads(principal.platform_mappings) if principal.platform_mappings else {},
                    "media_buy_count": media_buy_count,
                    "created_at": principal.created_at,
                }
                principals_list.append(principal_dict)

            # The template expects this to be under the 'advertisers' key
            # since principals are advertisers in the UI
            return render_template(
                advertisers=principals_list,
                show_advertisers_tab=True)

    except Exception as e:
        logger.error(f"Error listing principals: {e}", exc_info=True)
        flash("Error loading advertisers", "error")
        return redirect(url_for("core.index"))


@principals_bp.route("/principals/create", methods=["GET", "POST"])
def create_principal(tenant_id):
    """Create a new principal (advertiser) for a tenant."""
    if request.method == "GET":
        # Get tenant info for GAM configuration
        with get_db_session() as db_session:
            tenant = db_session.query(Tenant).first()
            if not tenant:
                flash("Tenant not found", "error")
                return redirect(url_for("core.index"))

            # Check if GAM is configured
            from src.admin.utils import get_tenant_config_from_db

            config = get_tenant_config_from_db(tenant_id)
            gam_config = config.get("adapters", {}).get("google_ad_manager", {})
            has_gam = gam_config.get("enabled", False)

            return render_template(
                tenant_name=tenant.name,
                has_gam=has_gam)

    # POST - Create the principal
    try:
        principal_name = request.form.get("name", "").strip()
        if not principal_name:
            flash("Principal name is required", "error")
            return redirect(request.url)

        # Generate unique ID and token
        principal_id = f"prin_{uuid.uuid4().hex[:8]}"
        access_token = f"tok_{secrets.token_urlsafe(32)}"

        # Build platform mappings
        platform_mappings = {}

        # GAM advertiser mapping
        gam_advertiser_id = request.form.get("gam_advertiser_id", "").strip()
        if gam_advertiser_id:
            platform_mappings["google_ad_manager"] = {
                "advertiser_id": gam_advertiser_id,
                "enabled": True,
            }

        # Mock adapter mapping (for testing)
        if request.form.get("enable_mock"):
            platform_mappings["mock"] = {
                "advertiser_id": f"mock_{principal_id}",
                "enabled": True,
            }

        with get_db_session() as db_session:
            # Check if principal name already exists
            existing = db_session.query(Principal).filter_by(name=principal_name).first()
            if existing:
                flash(f"An advertiser named '{principal_name}' already exists", "error")
                return redirect(request.url)

            # Create the principal
            principal = Principal(principal_id=principal_id,
                name=principal_name,
                access_token=access_token,
                platform_mappings=json.dumps(platform_mappings),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC))

            db_session.add(principal)
            db_session.commit()

            flash(f"Advertiser '{principal_name}' created successfully", "success")
            return redirect(url_for("tenants.dashboard"))

    except Exception as e:
        logger.error(f"Error creating principal: {e}", exc_info=True)
        flash("Error creating advertiser", "error")
        return redirect(request.url)


@principals_bp.route("/principal/<principal_id>/update_mappings", methods=["POST"])
def update_mappings(tenant_id, principal_id):
    """Update principal platform mappings."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request"}), 400

        platform_mappings = data.get("platform_mappings", {})

        with get_db_session() as db_session:
            principal = db_session.query(Principal).filter_by(principal_id=principal_id).first()

            if not principal:
                return jsonify({"error": "Principal not found"}), 404

            # Update mappings
            principal.platform_mappings = json.dumps(platform_mappings)
            principal.updated_at = datetime.now(UTC)
            db_session.commit()

            return jsonify(
                {
                    "success": True,
                    "message": "Platform mappings updated successfully",
                }
            )

    except Exception as e:
        logger.error(f"Error updating principal mappings: {e}", exc_info=True)
        return jsonify({"error": "Failed to update mappings"}), 500


@principals_bp.route("/api/gam/get-advertisers", methods=["POST"])
def get_gam_advertisers(tenant_id):
    """Get list of advertisers from GAM for a tenant."""
    try:
        from src.adapters.google_ad_manager import GoogleAdManager

        # Get tenant configuration
        with get_db_session() as db_session:
            tenant = db_session.query(Tenant).first()
            if not tenant:
                return jsonify({"error": "Tenant not found"}), 404

            from src.admin.utils import get_tenant_config_from_db

            config = get_tenant_config_from_db(tenant_id)
            gam_config = config.get("adapters", {}).get("google_ad_manager", {})

            if not gam_config.get("enabled"):
                return jsonify({"error": "Google Ad Manager not configured"}), 400

            # Initialize GAM adapter with tenant config
            try:
                # Create a mock principal for GAM initialization
                mock_principal = {
                    "principal_id": "system",
                    "name": "System",
                    "platform_mappings": {},
                }

                adapter = GoogleAdManager(
                    principal=mock_principal,
                    config=gam_config,
                    dry_run=False)

                # Get advertisers (companies) from GAM
                advertisers = adapter.get_advertisers()

                return jsonify(
                    {
                        "success": True,
                        "advertisers": advertisers,
                    }
                )

            except Exception as gam_error:
                logger.error(f"GAM API error: {gam_error}")
                return jsonify({"error": f"Failed to fetch advertisers: {str(gam_error)}"}), 500

    except Exception as e:
        logger.error(f"Error getting GAM advertisers: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
