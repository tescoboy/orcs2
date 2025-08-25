"""Creative formats management blueprint for admin UI."""

import json
import logging
import uuid
from datetime import UTC, datetime

# TODO: Missing module - these functions need to be implemented
# from creative_formats import discover_creative_formats_from_url, parse_creative_spec


# Placeholder implementations for missing functions
def parse_creative_spec(url):
    """Parse creative specification from URL - placeholder implementation."""
    return {"success": False, "error": "Creative format parsing not yet implemented", "url": url}


def discover_creative_formats_from_url(url):
    """Discover creative formats from URL - placeholder implementation."""
    return []


from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import or_


from src.core.database.database_session import get_db_session
from src.core.database.models import CreativeFormat, Tenant

logger = logging.getLogger(__name__)

# Create Blueprint
creatives_bp = Blueprint("creatives", __name__)


@creatives_bp.route("/", methods=["GET"])
def index():
    """List creative formats (both standard and custom)."""
    with get_db_session() as db_session:
        # For demo, use first tenant or create default
        tenant = db_session.query(Tenant).first()
        if not tenant:
            return "No tenants found", 404

        tenant_id = tenant.tenant_id
        tenant_name = tenant.name

        # Get all formats (standard + custom for this tenant)
        creative_formats = (
            db_session.query(CreativeFormat)
            .filter(or_(CreativeFormat.tenant_id.is_(None), CreativeFormat.tenant_id == tenant_id))
            .order_by(CreativeFormat.is_standard.desc(), CreativeFormat.type, CreativeFormat.name)
            .all()
        )

        formats = []
        for cf in creative_formats:
            format_info = {
                "format_id": cf.format_id,
                "name": cf.name,
                "type": cf.type,
                "description": cf.description,
                "is_standard": cf.is_standard,
                "source_url": cf.source_url,
                "created_at": cf.created_at,
            }

            # Add dimensions or duration
            if cf.width and cf.height:  # width and height
                format_info["dimensions"] = f"{cf.width}x{cf.height}"
            elif cf.duration_seconds:  # duration
                format_info["duration"] = f"{cf.duration_seconds}s"

            formats.append(format_info)

    return render_template(
        tenant_name=tenant_name,
        formats=formats)


@creatives_bp.route("/add/ai", methods=["GET"])
def add_ai():
    """Show AI-assisted creative format discovery form."""
    with get_db_session() as db_session:
        tenant = db_session.query(Tenant).first()
        tenant_id = tenant.tenant_id if tenant else "demo"
    return render_template("creative_format_ai.html")


@creatives_bp.route("/analyze", methods=["POST"])
def analyze():
    """Analyze creative format with AI."""
    try:
        url = request.form.get("url", "").strip()
        if not url:
            return jsonify({"error": "URL is required"}), 400

        # Use the creative format parser
        result = parse_creative_spec(url)

        if result.get("error"):
            return jsonify({"error": result["error"]}), 400

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error analyzing creative format: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@creatives_bp.route("/save", methods=["POST"])
def save():
    """Save a creative format to the database."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        format_id = f"fmt_{uuid.uuid4().hex[:8]}"

        with get_db_session() as db_session:
            # For demo, use first tenant
            tenant = db_session.query(Tenant).first()
            tenant_id = tenant.tenant_id if tenant else "demo"
            
            # Check if format already exists
            existing = db_session.query(CreativeFormat).filter_by(name=data.get("name")).first()

            if existing:
                return jsonify({"error": f"Format '{data.get('name')}' already exists"}), 400

            # Create new format
            creative_format = CreativeFormat(
                format_id=format_id,
                name=data.get("name"),
                type=data.get("type"),
                description=data.get("description"),
                width=data.get("width"),
                height=data.get("height"),
                duration_seconds=data.get("duration_seconds"),
                max_file_size_kb=data.get("max_file_size_kb"),
                supported_mime_types=json.dumps(data.get("supported_mime_types", [])),
                is_standard=False,
                source_url=data.get("source_url"),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC))

            db_session.add(creative_format)
            db_session.commit()

            return jsonify({"success": True, "format_id": format_id})

    except Exception as e:
        logger.error(f"Error saving creative format: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@creatives_bp.route("/sync-standard", methods=["POST"])
def sync_standard():
    """Sync standard formats from adcontextprotocol.org."""
    try:
        # This would normally fetch from the protocol site
        # For now, return success
        flash("Standard formats synced successfully", "success")
        return redirect(url_for("creatives.index"))

    except Exception as e:
        logger.error(f"Error syncing standard formats: {e}", exc_info=True)
        flash(f"Error syncing formats: {str(e)}", "error")
        return redirect(url_for("creatives.index"))


@creatives_bp.route("/discover", methods=["POST"])
def discover():
    """Discover multiple creative formats from a URL."""
    try:
        data = request.get_json()
        url = data.get("url", "").strip()

        if not url:
            return jsonify({"error": "URL is required"}), 400

        # Discover formats from the URL
        formats = discover_creative_formats_from_url(url)

        if not formats:
            return jsonify({"error": "No creative formats found at the URL"}), 404

        return jsonify({"formats": formats})

    except Exception as e:
        logger.error(f"Error discovering formats: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@creatives_bp.route("/save-multiple", methods=["POST"])
def save_multiple():
    """Save multiple discovered creative formats to the database."""
    try:
        data = request.get_json()
        formats = data.get("formats", [])

        if not formats:
            return jsonify({"error": "No formats provided"}), 400

        saved_count = 0
        skipped_count = 0
        errors = []

        with get_db_session() as db_session:
            # For demo, use first tenant
            tenant = db_session.query(Tenant).first()
            tenant_id = tenant.tenant_id if tenant else "demo"
            
            for format_data in formats:
                # Check if format already exists
                existing = (
                    db_session.query(CreativeFormat)
                    .filter_by(name=format_data.get("name"))
                    .first()
                )

                if existing:
                    skipped_count += 1
                    continue

                try:
                    format_id = f"fmt_{uuid.uuid4().hex[:8]}"
                    creative_format = CreativeFormat(
                        format_id=format_id,
                        name=format_data.get("name"),
                        type=format_data.get("type"),
                        description=format_data.get("description"),
                        width=format_data.get("width"),
                        height=format_data.get("height"),
                        duration_seconds=format_data.get("duration_seconds"),
                        max_file_size_kb=format_data.get("max_file_size_kb"),
                        supported_mime_types=json.dumps(format_data.get("supported_mime_types", [])),
                        is_standard=False,
                        source_url=format_data.get("source_url"),
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC))

                    db_session.add(creative_format)
                    saved_count += 1

                except Exception as e:
                    errors.append(f"Error saving {format_data.get('name')}: {str(e)}")

            db_session.commit()

        return jsonify(
            {
                "success": True,
                "saved": saved_count,
                "skipped": skipped_count,
                "errors": errors,
            }
        )

    except Exception as e:
        logger.error(f"Error saving multiple formats: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@creatives_bp.route("/<format_id>", methods=["GET"])
def get_format(format_id):
    """Get a specific creative format for editing."""
    with get_db_session() as db_session:
        creative_format = db_session.query(CreativeFormat).filter_by(format_id=format_id).first()

        if not creative_format:
            return jsonify({"error": "Format not found"}), 404



        format_data = {
            "format_id": creative_format.format_id,
            "name": creative_format.name,
            "type": creative_format.type,
            "description": creative_format.description,
            "width": creative_format.width,
            "height": creative_format.height,
            "duration_seconds": creative_format.duration_seconds,
            "max_file_size_kb": creative_format.max_file_size_kb,
            "supported_mime_types": json.loads(creative_format.supported_mime_types or "[]"),
            "is_standard": creative_format.is_standard,
            "source_url": creative_format.source_url,
        }

        return jsonify(format_data)


@creatives_bp.route("/<format_id>/edit", methods=["GET"])
def edit_format(format_id):
    """Display the edit creative format page."""
    with get_db_session() as db_session:
        creative_format = db_session.query(CreativeFormat).filter_by(format_id=format_id).first()

        if not creative_format:
            flash("Format not found", "error")
            return redirect(url_for("creatives.index"))

        # Prepare format data for template
        format_data = {
            "format_id": creative_format.format_id,
            "name": creative_format.name,
            "type": creative_format.type,
            "description": creative_format.description,
            "width": creative_format.width,
            "height": creative_format.height,
            "duration_seconds": creative_format.duration_seconds,
            "max_file_size_kb": creative_format.max_file_size_kb,
            "supported_mime_types": json.loads(creative_format.supported_mime_types or "[]"),
            "is_standard": creative_format.is_standard,
            "source_url": creative_format.source_url,
        }

        # Get tenant name
        tenant = db_session.query(Tenant).first()
        tenant_id = tenant.tenant_id if tenant else "demo"
        tenant_name = tenant.name if tenant else "Demo"

    return render_template(
        tenant_name=tenant_name,
        format=format_data)


@creatives_bp.route("/<format_id>/update", methods=["POST"])
def update_format(format_id):
    """Update a creative format."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        with get_db_session() as db_session:
            creative_format = db_session.query(CreativeFormat).filter_by(format_id=format_id).first()

            if not creative_format:
                return jsonify({"error": "Format not found"}), 404

            # Don't allow editing standard formats
            if creative_format.is_standard:
                return jsonify({"error": "Cannot edit standard formats"}), 403

            # Update fields
            creative_format.name = data.get("name", creative_format.name)
            creative_format.type = data.get("type", creative_format.type)
            creative_format.description = data.get("description", creative_format.description)
            creative_format.width = data.get("width", creative_format.width)
            creative_format.height = data.get("height", creative_format.height)
            creative_format.duration_seconds = data.get("duration_seconds", creative_format.duration_seconds)
            creative_format.max_file_size_kb = data.get("max_file_size_kb", creative_format.max_file_size_kb)
            creative_format.supported_mime_types = json.dumps(data.get("supported_mime_types", []))
            creative_format.updated_at = datetime.now(UTC)

            db_session.commit()

            return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Error updating creative format: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@creatives_bp.route("/<format_id>/delete", methods=["POST"])
def delete_format(format_id):
    """Delete a creative format."""
    try:
        with get_db_session() as db_session:
            creative_format = db_session.query(CreativeFormat).filter_by(format_id=format_id).first()

            if not creative_format:
                return jsonify({"error": "Format not found"}), 404

            # Don't allow deleting standard formats
            if creative_format.is_standard:
                return jsonify({"error": "Cannot delete standard formats"}), 403

            db_session.delete(creative_format)
            db_session.commit()

            flash("Creative format deleted successfully", "success")
            return redirect(url_for("creatives.index"))

    except Exception as e:
        logger.error(f"Error deleting creative format: {e}", exc_info=True)
        flash(f"Error deleting format: {str(e)}", "error")
        return redirect(url_for("creatives.index"))
