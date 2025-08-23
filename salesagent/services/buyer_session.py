"""Session-lite basket service for buyer product selection."""

import time
from typing import Dict, List, Set, Optional
from flask import request, Response
import secrets


# In-memory store: session_id -> set of product keys
_buyer_sessions: Dict[str, Dict[str, dict]] = {}
_session_timestamps: Dict[str, float] = {}

# TTL for sessions (24 hours)
SESSION_TTL = 24 * 60 * 60


def get_or_create_session_id(request, response) -> str:
    """Get existing session ID or create a new one."""
    session_id = request.cookies.get('buyer_session_id')
    
    if not session_id or not _is_valid_session(session_id):
        session_id = secrets.token_urlsafe(32)
        response.set_cookie('buyer_session_id', session_id, max_age=SESSION_TTL, httponly=True)
        _buyer_sessions[session_id] = {}
        _session_timestamps[session_id] = time.time()
    
    return session_id


def _is_valid_session(session_id: str) -> bool:
    """Check if session exists and is not expired."""
    if session_id not in _buyer_sessions:
        return False
    
    timestamp = _session_timestamps.get(session_id, 0)
    if time.time() - timestamp > SESSION_TTL:
        # Clean up expired session
        _cleanup_session(session_id)
        return False
    
    return True


def _cleanup_session(session_id: str):
    """Remove expired session."""
    _buyer_sessions.pop(session_id, None)
    _session_timestamps.pop(session_id, None)


def add_to_selection(session_id: str, product_key: str, product_snapshot: dict) -> bool:
    """Add a product to the buyer's selection basket."""
    if not _is_valid_session(session_id):
        return False
    
    _buyer_sessions[session_id][product_key] = product_snapshot
    _session_timestamps[session_id] = time.time()
    return True


def remove_from_selection(session_id: str, product_key: str) -> bool:
    """Remove a product from the buyer's selection basket."""
    if not _is_valid_session(session_id):
        return False
    
    if product_key in _buyer_sessions[session_id]:
        del _buyer_sessions[session_id][product_key]
        _session_timestamps[session_id] = time.time()
        return True
    
    return False


def list_selection(session_id: str) -> List[dict]:
    """Get list of selected products for a session."""
    if not _is_valid_session(session_id):
        return []
    
    return list(_buyer_sessions[session_id].values())


def get_selection_count(session_id: str) -> int:
    """Get count of selected products."""
    if not _is_valid_session(session_id):
        return 0
    
    return len(_buyer_sessions[session_id])


def clear_selection(session_id: str) -> bool:
    """Clear all selected products for a session."""
    if not _is_valid_session(session_id):
        return False
    
    _buyer_sessions[session_id].clear()
    _session_timestamps[session_id] = time.time()
    return True


def cleanup_expired_sessions():
    """Clean up all expired sessions (helper function)."""
    current_time = time.time()
    expired_sessions = [
        session_id for session_id, timestamp in _session_timestamps.items()
        if current_time - timestamp > SESSION_TTL
    ]
    
    for session_id in expired_sessions:
        _cleanup_session(session_id)
