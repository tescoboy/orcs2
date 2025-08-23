"""Buyer payload router for ad payload export."""

from flask import Blueprint, request, render_template, jsonify, make_response, abort
from typing import Dict, Any, Optional

from src.services.buyer_campaign_service import BuyerCampaignService
from services.ad_payload_mapper import AdPayloadMapper

buyer_payload_bp = Blueprint('buyer_payload', __name__, url_prefix='/buyer/campaign')
campaign_service = BuyerCampaignService()
payload_mapper = AdPayloadMapper()


@buyer_payload_bp.route("/<int:campaign_id>/payload.json")
def get_payload_json(campaign_id: int):
    """Get campaign payload as JSON."""
    # Get campaign summary
    summary = campaign_service.get_campaign_summary(campaign_id)
    if not summary:
        abort(404, description="Campaign not found")
    
    # Map to payload format
    try:
        payload = payload_mapper.map_campaign_to_payload(summary, summary.get('products_with_snapshots', []))
        
        # Validate payload
        errors = payload_mapper.validate_payload(payload)
        if errors:
            return jsonify({"error": "Invalid payload", "details": errors}), 500
        
        # Format as compact JSON
        json_content = payload_mapper.format_payload_json(payload, pretty=False)
        
        # Check if download is requested
        if request.args.get('download') == '1':
            response = make_response(json_content)
            response.headers['Content-Type'] = 'application/json'
            
            # Generate filename
            campaign_name = summary.get('campaign', {}).get('name') if isinstance(summary.get('campaign'), dict) else getattr(summary.get('campaign'), 'name', None)
            filename = payload_mapper.generate_filename(campaign_id, campaign_name)
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        else:
            # Return as regular JSON response
            return jsonify(payload)
            
    except Exception as e:
        return jsonify({"error": "Failed to generate payload", "message": str(e)}), 500


@buyer_payload_bp.route("/<int:campaign_id>/payload")
def get_payload_view(campaign_id: int):
    """Get campaign payload view page."""
    # Get campaign summary
    summary = campaign_service.get_campaign_summary(campaign_id)
    if not summary:
        abort(404, description="Campaign not found")
    
    # Map to payload format
    try:
        payload = payload_mapper.map_campaign_to_payload(summary, summary.get('products_with_snapshots', []))
        
        # Validate payload
        errors = payload_mapper.validate_payload(payload)
        if errors:
            return render_template("ui/buyer/payload_error.html", 
                                 campaign_id=campaign_id, 
                                 errors=errors), 500
        
        # Format as pretty JSON
        pretty_json = payload_mapper.format_payload_json(payload, pretty=True)
        
        # Get campaign name for page title
        campaign_name = summary.get('campaign', {}).get('name') if isinstance(summary.get('campaign'), dict) else getattr(summary.get('campaign'), 'name', 'Unknown Campaign')
        
        return render_template("ui/buyer/payload_view.html",
                             campaign_id=campaign_id,
                             campaign_name=campaign_name,
                             payload_json=pretty_json,
                             line_items_count=len(payload.get('line_items', [])))
        
    except Exception as e:
        return render_template("ui/buyer/payload_error.html", 
                             campaign_id=campaign_id, 
                             errors=[f"Failed to generate payload: {str(e)}"]), 500


@buyer_payload_bp.route("/<int:campaign_id>/payload/validate")
def validate_payload(campaign_id: int):
    """Validate campaign payload structure."""
    # Get campaign summary
    summary = campaign_service.get_campaign_summary(campaign_id)
    if not summary:
        return jsonify({"valid": False, "errors": ["Campaign not found"]}), 404
    
    try:
        # Map to payload format
        payload = payload_mapper.map_campaign_to_payload(summary, summary.get('products_with_snapshots', []))
        
        # Validate payload
        errors = payload_mapper.validate_payload(payload)
        
        return jsonify({
            "valid": len(errors) == 0,
            "errors": errors,
            "line_items_count": len(payload.get('line_items', [])),
            "campaign_name": payload.get('campaign_name', '')
        })
        
    except Exception as e:
        return jsonify({
            "valid": False,
            "errors": [f"Validation failed: {str(e)}"]
        }), 500


def get_payload_summary(campaign_id: int) -> Optional[Dict[str, Any]]:
    """Get a brief summary of the payload for display purposes."""
    try:
        summary = campaign_service.get_campaign_summary(campaign_id)
        if not summary:
            return None
        
        payload = payload_mapper.map_campaign_to_payload(summary, summary.get('products_with_snapshots', []))
        
        return {
            "campaign_name": payload.get('campaign_name', ''),
            "line_items_count": len(payload.get('line_items', [])),
            "budget_total": payload.get('budget_total', 0),
            "flight": payload.get('flight', {}),
            "has_objective": bool(payload.get('objective'))
        }
        
    except Exception:
        return None
