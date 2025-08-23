"""Core prompt loading and validation functionality."""

import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class PromptLoaderCore:
    """Core functionality for loading and validating AI prompt templates."""
    
    def __init__(self):
        self._default_prompt_cache: Optional[str] = None
    
    def _get_default_prompt(self) -> str:
        """Load the default prompt template from file with caching."""
        if self._default_prompt_cache is None:
            prompt_path = Path(__file__).parent.parent.parent.parent / "ai" / "prompts" / "default_product_ranking.txt"
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    self._default_prompt_cache = f.read().strip()
            except FileNotFoundError:
                raise FileNotFoundError(f"Default prompt template not found at {prompt_path}")
            except Exception as e:
                raise RuntimeError(f"Error reading default prompt template: {e}")
        
        return self._default_prompt_cache
    
    def validate_template(self, template: str) -> Tuple[bool, List[str]]:
        """Validate that a template contains required placeholders."""
        required_placeholders = ['{{PROMPT}}', '{{PRODUCTS_JSON}}', '{{MAX_RESULTS}}']
        optional_placeholders = ['{{LOCALE}}', '{{CURRENCY}}']
        
        errors = []
        warnings = []
        
        # Check required placeholders
        for placeholder in required_placeholders:
            if placeholder not in template:
                errors.append(f"Missing required placeholder: {placeholder}")
        
        # Check optional placeholders
        for placeholder in optional_placeholders:
            if placeholder not in template:
                warnings.append(f"Missing optional placeholder: {placeholder}")
        
        return len(errors) == 0, errors + warnings
