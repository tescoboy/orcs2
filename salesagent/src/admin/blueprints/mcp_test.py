"""McpTest management blueprint."""

import logging

from flask import Blueprint, jsonify


logger = logging.getLogger(__name__)

# Create blueprint
mcp_test_bp = Blueprint("mcp_test", __name__)


@mcp_test_bp.route("/mcp-test", methods=["GET"])
def mcp_test():
    """TODO: Extract implementation from admin_ui.py."""
    # Placeholder implementation
    return jsonify({"error": "Not yet implemented"}), 501
