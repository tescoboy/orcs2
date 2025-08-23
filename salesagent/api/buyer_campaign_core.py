"""Core buyer campaign router functionality."""

from typing import Dict, Any, Optional
from datetime import datetime, date
from flask import request, render_template, redirect, url_for, flash, make_response

from src.services.buyer_campaign_service import BuyerCampaignService
from services.buyer_session import get_or_create_session_id, list_selection, get_selection_count

campaign_service = BuyerCampaignService()

# In-memory temp store for wizard data (session_id -> data)
_wizard_temp_store = {}


class BuyerCampaignCore:
    """Core functionality for buyer campaign operations."""
    
    @staticmethod
    def get_session_and_check_selection():
        """Get session ID and check if user has products in selection."""
        response = make_response()
        session_id = get_or_create_session_id(request, response)
        
        selection_count = get_selection_count(session_id)
        if selection_count == 0:
            flash("Please add products to your selection before creating a campaign", "warning")
            return None, None, None
        
        return session_id, response, selection_count
    
    @staticmethod
    def validate_step1_data(name: str) -> bool:
        """Validate Step 1 form data."""
        if not name or not name.strip():
            flash("Campaign name is required", "danger")
            return False
        return True
    
    @staticmethod
    def store_step1_data(session_id: str, name: str, objective: str):
        """Store Step 1 data in temp store."""
        _wizard_temp_store[session_id] = {
            'step1': {
                'name': name,
                'objective': objective
            }
        }
    
    @staticmethod
    def validate_step2_data(start_date: date, end_date: date, budget_total: float, name: str) -> bool:
        """Validate Step 2 form data."""
        errors = campaign_service.validate_campaign_data(name, start_date, end_date, budget_total)
        
        if errors:
            for error in errors:
                flash(error, "danger")
            return False
        return True
    
    @staticmethod
    def store_step2_data(session_id: str, start_date: date, end_date: date, budget_total: float):
        """Store Step 2 data in temp store."""
        _wizard_temp_store[session_id]['step2'] = {
            'start_date': start_date,
            'end_date': end_date,
            'budget_total': budget_total
        }
    
    @staticmethod
    def get_wizard_data(session_id: str) -> Optional[Dict[str, Any]]:
        """Get wizard data for a session."""
        return _wizard_temp_store.get(session_id)
    
    @staticmethod
    def clear_wizard_data(session_id: str):
        """Clear wizard data for a session."""
        if session_id in _wizard_temp_store:
            del _wizard_temp_store[session_id]
    
    @staticmethod
    def create_and_finalize_campaign(session_id: str, step1_data: Dict, step2_data: Dict) -> Optional[int]:
        """Create and finalize a campaign."""
        try:
            # Create campaign
            campaign_id = campaign_service.create_draft_campaign(
                name=step1_data['name'],
                objective=step1_data['objective'],
                start_date=step2_data['start_date'],
                end_date=step2_data['end_date'],
                budget_total=step2_data['budget_total']
            )
            
            # Finalize campaign
            if campaign_service.finalize_campaign(campaign_id, session_id):
                return campaign_id
            else:
                flash("Failed to create campaign", "danger")
                return None
                
        except Exception as e:
            flash(f"Error creating campaign: {str(e)}", "danger")
            return None
