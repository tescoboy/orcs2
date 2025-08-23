"""Buyer campaign router for 3-step wizard."""

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, make_response
from typing import Dict, Any, Optional
from datetime import datetime, date
import json

from src.services.buyer_campaign_service import BuyerCampaignService
from services.buyer_session import get_or_create_session_id, list_selection, get_selection_count
from .buyer_campaign_core import BuyerCampaignCore

buyer_campaign_bp = Blueprint('buyer_campaign', __name__, url_prefix='/buyer/campaign')
campaign_service = BuyerCampaignService()


@buyer_campaign_bp.route("/new")
def new_campaign():
    """Step 1: Campaign details form."""
    session_id, response, selection_count = BuyerCampaignCore.get_session_and_check_selection()
    
    if session_id is None:
        return redirect(url_for('buyer_ui.search'))
    
    return render_template("ui/buyer/campaign_step1.html", 
                         selection_count=selection_count), 200, {'Set-Cookie': response.headers.get('Set-Cookie', '')}


@buyer_campaign_bp.route("/step1", methods=["POST"])
def step1_submit():
    """Handle Step 1 form submission."""
    response = make_response()
    session_id = get_or_create_session_id(request, response)
    
    name = request.form.get('name', '').strip()
    objective = request.form.get('objective', '').strip()
    
    # Validation
    if not BuyerCampaignCore.validate_step1_data(name):
        return render_template("ui/buyer/campaign_step1.html", 
                             name=name, objective=objective), 400, {'Set-Cookie': response.headers.get('Set-Cookie', '')}
    
    # Store in temp store
    BuyerCampaignCore.store_step1_data(session_id, name, objective)
    
    return redirect(url_for('buyer_campaign.step2')), 302, {'Set-Cookie': response.headers.get('Set-Cookie', '')}


@buyer_campaign_bp.route("/step2")
def step2():
    """Step 2: Flighting and budget form."""
    response = make_response()
    session_id = get_or_create_session_id(request, response)
    
    # Check if we have step1 data
    wizard_data = BuyerCampaignCore.get_wizard_data(session_id)
    if not wizard_data or 'step1' not in wizard_data:
        flash("Please start with Step 1", "warning")
        return redirect(url_for('buyer_campaign.new_campaign'))
    
    step1_data = wizard_data['step1']
    
    return render_template("ui/buyer/campaign_step2.html", 
                         name=step1_data['name'], 
                         objective=step1_data['objective']), 200, {'Set-Cookie': response.headers.get('Set-Cookie', '')}


@buyer_campaign_bp.route("/step2", methods=["POST"])
def step2_submit():
    """Handle Step 2 form submission."""
    response = make_response()
    session_id = get_or_create_session_id(request, response)
    
    # Check if we have step1 data
    wizard_data = BuyerCampaignCore.get_wizard_data(session_id)
    if not wizard_data or 'step1' not in wizard_data:
        flash("Please start with Step 1", "warning")
        return redirect(url_for('buyer_campaign.new_campaign'))
    
    try:
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        budget_total = float(request.form.get('budget_total', 0))
    except (ValueError, TypeError):
        flash("Invalid date or budget format", "danger")
        return render_template("ui/buyer/campaign_step2.html"), 400, {'Set-Cookie': response.headers.get('Set-Cookie', '')}
    
    # Validation
    if not BuyerCampaignCore.validate_step2_data(start_date, end_date, budget_total, wizard_data['step1']['name']):
        return render_template("ui/buyer/campaign_step2.html"), 400, {'Set-Cookie': response.headers.get('Set-Cookie', '')}
    
    # Store step2 data
    BuyerCampaignCore.store_step2_data(session_id, start_date, end_date, budget_total)
    
    return redirect(url_for('buyer_campaign.step3')), 302, {'Set-Cookie': response.headers.get('Set-Cookie', '')}


@buyer_campaign_bp.route("/step3")
def step3():
    """Step 3: Review and confirm."""
    response = make_response()
    session_id = get_or_create_session_id(request, response)
    
    # Check if we have all previous data
    wizard_data = BuyerCampaignCore.get_wizard_data(session_id)
    if not wizard_data or 'step1' not in wizard_data or 'step2' not in wizard_data:
        flash("Please complete previous steps", "warning")
        return redirect(url_for('buyer_campaign.new_campaign'))
    
    # Get selected products
    selected_products = list_selection(session_id)
    if not selected_products:
        flash("No products selected. Please add products to continue.", "warning")
        return redirect(url_for('buyer_ui.search'))
    
    step1_data = wizard_data['step1']
    step2_data = wizard_data['step2']
    
    return render_template("ui/buyer/campaign_step3.html",
                         name=step1_data['name'],
                         objective=step1_data['objective'],
                         start_date=step2_data['start_date'],
                         end_date=step2_data['end_date'],
                         budget_total=step2_data['budget_total'],
                         selected_products=selected_products), 200, {'Set-Cookie': response.headers.get('Set-Cookie', '')}


@buyer_campaign_bp.route("/confirm", methods=["POST"])
def confirm_campaign():
    """Create the campaign and redirect to summary."""
    response = make_response()
    session_id = get_or_create_session_id(request, response)
    
    # Check if we have all data
    wizard_data = BuyerCampaignCore.get_wizard_data(session_id)
    if not wizard_data or 'step1' not in wizard_data or 'step2' not in wizard_data:
        flash("Please complete all steps", "warning")
        return redirect(url_for('buyer_campaign.new_campaign'))
    
    # Check if we have products
    selected_products = list_selection(session_id)
    if not selected_products:
        flash("No products selected. Please add products to continue.", "warning")
        return redirect(url_for('buyer_ui.search'))
    
    step1_data = wizard_data['step1']
    step2_data = wizard_data['step2']
    
    # Create and finalize campaign
    campaign_id = BuyerCampaignCore.create_and_finalize_campaign(session_id, step1_data, step2_data)
    
    if campaign_id:
        # Clear temp store
        BuyerCampaignCore.clear_wizard_data(session_id)
        
        flash("Campaign created successfully!", "success")
        return redirect(url_for('buyer_campaign.campaign_summary', campaign_id=campaign_id)), 302, {'Set-Cookie': response.headers.get('Set-Cookie', '')}
    else:
        return redirect(url_for('buyer_campaign.step3')), 302, {'Set-Cookie': response.headers.get('Set-Cookie', '')}


@buyer_campaign_bp.route("/<int:campaign_id>/summary")
def campaign_summary(campaign_id: int):
    """Display campaign summary."""
    summary = campaign_service.get_campaign_summary(campaign_id)
    if not summary:
        flash("Campaign not found", "danger")
        return redirect(url_for('buyer_ui.search'))
    
    return render_template("ui/buyer/campaign_summary.html", summary=summary)
