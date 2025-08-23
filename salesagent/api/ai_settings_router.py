"""API router for AI settings management."""

import logging
from datetime import datetime
from typing import Optional

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify

from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant
from src.services.prompt_loader import PromptLoader

# Initialize prompt loader
prompt_loader = PromptLoader()

logger = logging.getLogger(__name__)

# Create Blueprint
ai_settings_bp = Blueprint("ai_settings", __name__, url_prefix="/tenant/<tenant_id>/settings")


@ai_settings_bp.route("/ai", methods=["GET"])
def ai_settings_page(tenant_id: str):
    """Render AI prompt settings page."""
    
    try:
        # Get tenant and current prompt
        with get_db_session() as session:
            tenant = session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            
            if not tenant:
                flash("Tenant not found", "error")
                return redirect(url_for("login_router.login"))
            
            # Get current prompt (custom or default)
            try:
                current_prompt = prompt_loader.get_tenant_prompt(tenant_id)
                is_custom = tenant.ai_prompt_template is not None and tenant.ai_prompt_template.strip()
            except Exception as e:
                logger.error(f"Failed to load prompt for tenant {tenant_id}: {str(e)}")
                current_prompt = "Error loading prompt template"
                is_custom = False
            
            # Get supported placeholders
            placeholders = [
                {"name": "{{PROMPT}}", "description": "The buyer's natural language brief", "required": True},
                {"name": "{{PRODUCTS_JSON}}", "description": "Available products as JSON", "required": True},
                {"name": "{{MAX_RESULTS}}", "description": "Maximum number of products to return", "required": True},
                {"name": "{{LOCALE}}", "description": "Optional locale for localization", "required": False},
                {"name": "{{CURRENCY}}", "description": "Optional currency for pricing context", "required": False}
            ]
            
            return render_template(
                "ui/settings/ai_prompt.html",
                tenant=tenant,
                current_prompt=current_prompt,
                is_custom=is_custom,
                placeholders=placeholders,
                last_updated=tenant.ai_prompt_updated_at
            )
            
    except Exception as e:
        logger.error(f"Error loading AI settings page for tenant {tenant_id}: {str(e)}")
        flash("Error loading AI settings", "error")
        return redirect(url_for("tenant_router.tenant_home", tenant_id=tenant_id))


@ai_settings_bp.route("/ai", methods=["POST"])
def save_ai_settings(tenant_id: str):
    """Save AI prompt template."""
    
    try:
        # Get form data
        new_prompt = request.form.get("prompt_template", "").strip()
        
        if not new_prompt:
            flash("Prompt template cannot be empty", "error")
            return redirect(url_for("ai_settings.ai_settings_page", tenant_id=tenant_id))
        
        # Validate the template
        validation_result = prompt_loader.validate_template(new_prompt)
        
        if not validation_result["valid"]:
            error_msg = "Template validation failed: " + "; ".join(validation_result["errors"])
            flash(error_msg, "error")
            return redirect(url_for("ai_settings.ai_settings_page", tenant_id=tenant_id))
        
        # Save to database
        with get_db_session() as session:
            tenant = session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            
            if not tenant:
                flash("Tenant not found", "error")
                return redirect(url_for("login_router.login"))
            
            tenant.ai_prompt_template = new_prompt
            tenant.ai_prompt_updated_at = datetime.utcnow()
            
            session.commit()
            
            flash("AI prompt template saved successfully", "success")
            
            # Log warnings if any
            if validation_result["warnings"]:
                warning_msg = "Warnings: " + "; ".join(validation_result["warnings"])
                flash(warning_msg, "warning")
            
            logger.info(f"AI prompt template updated for tenant {tenant_id}")
            
        return redirect(url_for("ai_settings.ai_settings_page", tenant_id=tenant_id))
        
    except Exception as e:
        logger.error(f"Error saving AI settings for tenant {tenant_id}: {str(e)}")
        flash("Error saving AI settings", "error")
        return redirect(url_for("ai_settings.ai_settings_page", tenant_id=tenant_id))


@ai_settings_bp.route("/ai/reset", methods=["POST"])
def reset_ai_settings(tenant_id: str):
    """Reset AI prompt template to default."""
    
    try:
        with get_db_session() as session:
            tenant = session.query(Tenant).filter_by(tenant_id=tenant_id).first()
            
            if not tenant:
                flash("Tenant not found", "error")
                return redirect(url_for("login_router.login"))
            
            # Reset to NULL so default template is used
            tenant.ai_prompt_template = None
            tenant.ai_prompt_updated_at = datetime.utcnow()
            
            session.commit()
            
            flash("AI prompt template reset to default", "success")
            logger.info(f"AI prompt template reset to default for tenant {tenant_id}")
            
        return redirect(url_for("ai_settings.ai_settings_page", tenant_id=tenant_id))
        
    except Exception as e:
        logger.error(f"Error resetting AI settings for tenant {tenant_id}: {str(e)}")
        flash("Error resetting AI settings", "error")
        return redirect(url_for("ai_settings.ai_settings_page", tenant_id=tenant_id))


@ai_settings_bp.route("/ai/preview", methods=["POST"])
def preview_ai_prompt(tenant_id: str):
    """Preview compiled AI prompt (optional endpoint for future use)."""
    
    try:
        template = request.json.get("template", "")
        sample_context = {
            "prompt": "Looking for premium homepage advertising opportunities",
            "products_json": '[{"product_id": "sample", "name": "Homepage Banner"}]',
            "max_results": "5",
            "locale": "en-US",
            "currency": "USD"
        }
        
        # Validate template
        validation_result = prompt_loader.validate_template(template)
        
        if not validation_result["valid"]:
            return jsonify({
                "success": False,
                "errors": validation_result["errors"]
            })
        
        # Try to compile with sample data
        try:
            compiled = prompt_loader.compile_prompt(template, sample_context)
            return jsonify({
                "success": True,
                "compiled_prompt": compiled,
                "warnings": validation_result.get("warnings", [])
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "errors": [f"Compilation failed: {str(e)}"]
            })
            
    except Exception as e:
        logger.error(f"Error previewing AI prompt: {str(e)}")
        return jsonify({
            "success": False,
            "errors": [f"Preview failed: {str(e)}"]
        })
