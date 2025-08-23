"""Flask Blueprint for AI settings management."""

from flask import Blueprint, request, render_template, flash, redirect, url_for, jsonify
from typing import Dict, List

from .ai_settings_core import AISettingsCore


class AISettingsRouter(AISettingsCore):
    """Flask Blueprint for AI settings management."""
    
    def __init__(self):
        super().__init__()
        self.blueprint = Blueprint('ai_settings', __name__)
        self._register_routes()
    
    def _register_routes(self):
        """Register the Flask routes."""
        @self.blueprint.route('/tenant/<tenant_id>/settings/ai', methods=['GET'])
        def get_ai_settings(tenant_id: str):
            try:
                tenant, current_prompt = self.get_tenant_and_prompt(tenant_id)
                return render_template('ui/settings/ai_prompt.html', 
                                     tenant=tenant, 
                                     current_prompt=current_prompt)
            except ValueError as e:
                flash(str(e), 'error')
                return redirect(url_for('index'))
        
        @self.blueprint.route('/tenant/<tenant_id>/settings/ai', methods=['POST'])
        def save_ai_settings(tenant_id: str):
            template = request.form.get('prompt_template', '').strip()
            
            success, errors = self.save_tenant_prompt(tenant_id, template)
            
            if success:
                flash('AI prompt template saved successfully!', 'success')
            else:
                for error in errors:
                    flash(error, 'error')
            
            return redirect(url_for('ai_settings.get_ai_settings', tenant_id=tenant_id))
        
        @self.blueprint.route('/tenant/<tenant_id>/settings/ai/reset', methods=['POST'])
        def reset_ai_settings(tenant_id: str):
            success, errors = self.reset_tenant_prompt(tenant_id)
            
            if success:
                flash('AI prompt template reset to default!', 'success')
            else:
                for error in errors:
                    flash(error, 'error')
            
            return redirect(url_for('ai_settings.get_ai_settings', tenant_id=tenant_id))
        
        @self.blueprint.route('/tenant/<tenant_id>/settings/ai/preview', methods=['POST'])
        def preview_ai_settings(tenant_id: str):
            template = request.form.get('prompt_template', '').strip()
            
            # Sample context for preview
            sample_context = {
                "PROMPT": "Sample campaign brief for preview",
                "PRODUCTS_JSON": '[{"id": "sample", "name": "Sample Product"}]',
                "MAX_RESULTS": "5",
                "LOCALE": "Locale: en-US\n",
                "CURRENCY": "Currency: USD\n"
            }
            
            success, errors, compiled = self.preview_prompt_compilation(template, sample_context)
            
            return jsonify({
                'success': success,
                'errors': errors,
                'compiled_preview': compiled
            })


# Create the blueprint instance
ai_settings_blueprint = AISettingsRouter().blueprint
