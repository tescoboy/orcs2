"""User management blueprint for admin UI."""

import logging
from datetime import UTC, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant, User

logger = logging.getLogger(__name__)

# Create Blueprint
users_bp = Blueprint("users", __name__, url_prefix="/tenant/<tenant_id>/users")


@users_bp.route("")
def list_users(tenant_id):
    """List users for a tenant."""
    with get_db_session() as db_session:
        tenant = db_session.query(Tenant).first()
        if not tenant:
            flash("Tenant not found", "error")
            return redirect(url_for("core.index"))

        users = db_session.query(User).order_by(User.email).all()

        users_list = []
        for user in users:
            users_list.append(
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                }
            )

        return render_template(
            users=users_list)


@users_bp.route("/add", methods=["POST"])
def add_user(tenant_id):
    """Add a new user to the tenant."""
    try:
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "viewer")

        if not email:
            flash("Email is required", "error")
            return redirect(url_for("users.list_users"))

        # Validate email format
        import re

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email format", "error")
            return redirect(url_for("users.list_users"))

        with get_db_session() as db_session:
            # Check if user already exists
            existing = db_session.query(User).filter_by(email=email).first()
            if existing:
                flash(f"User {email} already exists", "error")
                return redirect(url_for("users.list_users"))

            # Create new user
            import uuid

            user = User(user_id=f"user_{uuid.uuid4().hex[:8]}",
                email=email,
                role=role,
                is_active=True,
                created_at=datetime.now(UTC))

            db_session.add(user)
            db_session.commit()

            flash(f"User {email} added successfully", "success")

    except Exception as e:
        logger.error(f"Error adding user: {e}", exc_info=True)
        flash(f"Error adding user: {str(e)}", "error")

    return redirect(url_for("users.list_users"))


@users_bp.route("/<user_id>/toggle", methods=["POST"])
def toggle_user(tenant_id, user_id):
    """Toggle user active status."""
    try:
        with get_db_session() as db_session:
            user = db_session.query(User).filter_by(user_id=user_id).first()
            if not user:
                flash("User not found", "error")
                return redirect(url_for("users.list_users"))

            user.is_active = not user.is_active
            db_session.commit()

            status = "activated" if user.is_active else "deactivated"
            flash(f"User {user.email} {status}", "success")

    except Exception as e:
        logger.error(f"Error toggling user: {e}", exc_info=True)
        flash(f"Error toggling user: {str(e)}", "error")

    return redirect(url_for("users.list_users"))


@users_bp.route("/<user_id>/update_role", methods=["POST"])
def update_role(tenant_id, user_id):
    """Update user role."""
    try:
        new_role = request.form.get("role")
        if not new_role or new_role not in ["admin", "manager", "viewer"]:
            flash("Invalid role", "error")
            return redirect(url_for("users.list_users"))

        with get_db_session() as db_session:
            user = db_session.query(User).filter_by(user_id=user_id).first()
            if not user:
                flash("User not found", "error")
                return redirect(url_for("users.list_users"))

            user.role = new_role
            db_session.commit()

            flash(f"User {user.email} role updated to {new_role}", "success")

    except Exception as e:
        logger.error(f"Error updating user role: {e}", exc_info=True)
        flash(f"Error updating role: {str(e)}", "error")

    return redirect(url_for("users.list_users"))
