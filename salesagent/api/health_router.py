"""Health check router for application monitoring."""

from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)


@health_bp.route("/health")
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "orcs2-salesagent"
    })


@health_bp.route("/health/detailed")
def detailed_health_check():
    """Detailed health check with component status."""
    try:
        # Basic checks - can be extended with database, external services, etc.
        checks = {
            "database": "ok",  # TODO: Add actual DB check
            "orchestrator": "ok",  # TODO: Add orchestrator check
            "buyer_ui": "ok",  # TODO: Add buyer UI check
            "campaign_builder": "ok"  # TODO: Add campaign builder check
        }
        
        overall_status = "ok" if all(status == "ok" for status in checks.values()) else "degraded"
        
        return jsonify({
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "orcs2-salesagent",
            "checks": checks
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "orcs2-salesagent",
            "error": str(e)
        }), 500


@health_bp.route("/health/ready")
def readiness_check():
    """Readiness check for Kubernetes/container orchestration."""
    # This endpoint indicates the service is ready to receive traffic
    # Add any startup checks here (database migrations, config loading, etc.)
    return jsonify({
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "orcs2-salesagent"
    })


@health_bp.route("/health/live")
def liveness_check():
    """Liveness check for Kubernetes/container orchestration."""
    # This endpoint indicates the service is alive and should not be restarted
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "orcs2-salesagent"
    })
