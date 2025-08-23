"""Buyer UI router for product search and selection."""

from flask import Blueprint, request, render_template, jsonify, make_response
from typing import List, Optional

from services.buyer_search_service import search_products
from services.buyer_session import (
    get_or_create_session_id, add_to_selection, remove_from_selection,
    list_selection, get_selection_count, clear_selection
)

# Create Blueprint
buyer_ui_bp = Blueprint("buyer_ui", __name__, url_prefix="/buyer")


@buyer_ui_bp.route("/", methods=["GET"])
def buyer_search_page():
    """Render the buyer search page."""
    response = make_response(render_template("ui/buyer/search.html"))
    session_id = get_or_create_session_id(request, response)
    return response


@buyer_ui_bp.route("/search", methods=["POST"])
def search_products_htmx():
    """HTMX endpoint for product search."""
    prompt = request.form.get("prompt", "").strip()
    max_results = int(request.form.get("max_results", 50))
    
    # Get filter parameters
    include_tenant_ids = request.form.getlist("include_tenant_ids")
    exclude_tenant_ids = request.form.getlist("exclude_tenant_ids")
    include_agent_ids = request.form.getlist("include_agent_ids")
    
    # Convert empty lists to None
    include_tenant_ids = include_tenant_ids if include_tenant_ids else None
    exclude_tenant_ids = exclude_tenant_ids if exclude_tenant_ids else None
    include_agent_ids = include_agent_ids if include_agent_ids else None
    
    if not prompt:
        return render_template("ui/buyer/_results_grid.html", products=[], error="Please enter a search prompt")
    
    # Search for products
    products = search_products(
        prompt=prompt,
        max_results=max_results,
        include_tenant_ids=include_tenant_ids,
        exclude_tenant_ids=exclude_tenant_ids,
        include_agent_ids=include_agent_ids
    )
    
    # Add logging to see what products are being passed to template
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"UI Router: Passing {len(products)} products to template")
    for i, product in enumerate(products[:3]):
        logger.info(f"UI Product {i+1}: {product.get('name', 'NO_NAME')} from {product.get('publisher_name', 'NO_PUBLISHER')}")
        logger.info(f"  - Price: ${product.get('price_cpm', 0)} CPM")
        logger.info(f"  - Delivery: {product.get('delivery_type', 'NO_TYPE')}")
    
    return render_template("ui/buyer/_results_grid.html", products=products)


@buyer_ui_bp.route("/selection/add", methods=["POST"])
def add_to_selection_htmx():
    """HTMX endpoint to add product to selection."""
    response = make_response()
    session_id = get_or_create_session_id(request, response)
    
    product_key = request.form.get("product_key")
    product_data = {
        'id': request.form.get("product_id"),
        'name': request.form.get("product_name"),
        'publisher_name': request.form.get("publisher_name"),
        'publisher_tenant_id': request.form.get("publisher_tenant_id"),
        'price_cpm': float(request.form.get("price_cpm", 0)),
        'delivery_type': request.form.get("delivery_type"),
        'formats': request.form.getlist("formats"),
        'image_url': request.form.get("image_url"),
        'rationale': request.form.get("rationale", "")
    }
    
    if add_to_selection(session_id, product_key, product_data):
        count = get_selection_count(session_id)
        return jsonify({"success": True, "count": count})
    else:
        return jsonify({"success": False, "error": "Failed to add to selection"}), 400


@buyer_ui_bp.route("/selection/remove", methods=["POST"])
def remove_from_selection_htmx():
    """HTMX endpoint to remove product from selection."""
    response = make_response()
    session_id = get_or_create_session_id(request, response)
    
    product_key = request.form.get("product_key")
    
    if remove_from_selection(session_id, product_key):
        count = get_selection_count(session_id)
        return jsonify({"success": True, "count": count})
    else:
        return jsonify({"success": False, "error": "Failed to remove from selection"}), 400


@buyer_ui_bp.route("/selection", methods=["GET"])
def selection_drawer():
    """Render the selection drawer/sidebar."""
    response = make_response()
    session_id = get_or_create_session_id(request, response)
    
    selected_products = list_selection(session_id)
    count = get_selection_count(session_id)
    
    return render_template("ui/buyer/_selection_drawer.html", 
                         selected_products=selected_products, 
                         count=count)


@buyer_ui_bp.route("/selection/clear", methods=["POST"])
def clear_selection_htmx():
    """HTMX endpoint to clear all selected products."""
    response = make_response()
    session_id = get_or_create_session_id(request, response)
    
    if clear_selection(session_id):
        return jsonify({"success": True, "count": 0})
    else:
        return jsonify({"success": False, "error": "Failed to clear selection"}), 400
